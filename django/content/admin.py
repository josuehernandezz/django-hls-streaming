from django.contrib import admin
from django import forms
from django.conf import settings
from pathlib import Path
from .models import Video, CastMember, Genre
# Register your models here.

class VideoAdminForm(forms.ModelForm):
    # Replace the TextField with a Select listing files from ALLOWED_IMPORT_DIRS
    server_path = forms.ChoiceField(
        required=False,
        choices=[],
        help_text="Pick a file from the server-mounted imports directories.",
    )

    class Meta:
        model = Video
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        allowed_dirs = (getattr(settings, "ALLOWED_IMPORT_DIRS", []) or [])
        allowed_exts = set(e.lower() for e in getattr(settings, "ALLOWED_IMPORT_EXTS", [".mp4", ".m4v", ".mov", ".mkv", ".webm"]))

        files = []
        for base in allowed_dirs:
            base_path = Path(base).expanduser().resolve()
            if not base_path.is_dir():
                continue
            # Recursively list files under this dir
            for p in base_path.rglob("*"):
                if p.is_file() and p.suffix.lower() in allowed_exts:
                    # Value: full container path (e.g. /imports/SomeMovie.mp4)
                    # Label: readable "filename — parent"
                    files.append((str(p), f"{p.name} — {p.parent}"))

        files.sort(key=lambda t: t[1].lower())
        self.fields["server_path"].choices = [("", "— Select a server file —")] + files

    def clean(self):
        cleaned = super().clean()
        source_type = cleaned.get("source_type")
        server_path = cleaned.get("server_path")
        upload = cleaned.get("video")

        if source_type == "server":
            if not server_path:
                self.add_error("server_path", "Pick a server file.")
            # Ensure we don’t accidentally keep an uploaded file, since we’re in server mode
            cleaned["video"] = None
        else:
            # Upload mode
            if not upload:
                self.add_error("video", "Upload a video file.")
            # Clear any server path
            cleaned["server_path"] = ""

        return cleaned

    class Media:
        js = ("admin/video_toggle.js",)  # see step 3 below

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    def delete_queryset(self, request, queryset):
        # Perform custom deletion logic for each selected object
        for video in queryset:
            video.delete()  # Calls the custom delete method for each object

        # After custom delete logic, call the parent method to complete deletion
        super().delete_queryset(request, queryset)
        
    list_display = ('name', 'duration', 'status', 'is_running')
    form = VideoAdminForm

class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(Genre, GenreAdmin)

class CastMemberAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(CastMember, CastMemberAdmin)
