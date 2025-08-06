from django.contrib import admin
from .models import Video, CastMember, Genre
# Register your models here.


class VideoAdmin(admin.ModelAdmin):
    def delete_queryset(self, request, queryset):
        # Perform custom deletion logic for each selected object
        for video in queryset:
            video.delete()  # Calls the custom delete method for each object

        # After custom delete logic, call the parent method to complete deletion
        super().delete_queryset(request, queryset)
        
    list_display = ('name', 'duration', 'status', 'is_running')

admin.site.register(Video, VideoAdmin)

class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(Genre, GenreAdmin)

class CastMemberAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(CastMember, CastMemberAdmin)
