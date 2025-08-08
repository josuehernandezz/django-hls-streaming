import os
import math
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.db.models.signals import post_save
from django.db import transaction
from django.db import models
from django.utils.text import slugify
from django.dispatch import receiver
from django.conf import settings


def validate_mp4_extension(value):
    ext = os.path.splitext(value.name)[1]  # Get the file extension
    if ext.lower() != '.mp4':
        raise ValidationError("Only .mp4 files are allowed.")

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class CastMember(models.Model):
    name = models.CharField(max_length=200)
    bio = models.TextField()

    def __str__(self):
        return self.name

class Video(models.Model):
    PENDING = 'Pending'
    PROCESSING = 'Processing'
    COMPLETED = 'Completed'
    FAILED = 'Failed'
    
    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
  
    name = models.CharField(max_length=500)
    slug = models.SlugField(max_length=50, blank=True)
    description = models.TextField()
  
    video = models.FileField(upload_to="videos",validators=[validate_mp4_extension])
    thumbnail = models.ImageField(upload_to="thumbnails",null=True,blank=True)
    duration = models.CharField(max_length=20, blank=True,null=True)
    hls = models.CharField(max_length=500,blank=True,null=True)
  
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    errors = models.TextField(blank=True, null=True)
    is_running = models.BooleanField(default=False)

    release_year = models.PositiveIntegerField(null=True, blank=True)
    genres = models.ManyToManyField(Genre, blank=True)
    cast = models.ManyToManyField(CastMember, blank=True)

    def __str__(self):
        return str(self.name)
    
    def delete(self):
        # Delete the associated video file before the model instance is deleted
        if self.video:
            self.video.delete(save=False)  # This deletes the video file

        # Delete the thumbnail
        if self.thumbnail:
            self.thumbnail.delete(save=False)

        # Delete the corresponding HLS files (m3u8 and segments)
        if self.hls:
            # Assuming the hls file path is relative to MEDIA_ROOT
            hls_playlist_path = os.path.join(settings.MEDIA_ROOT, self.hls)
            
            # Check if the playlist exists and delete it
            if os.path.exists(hls_playlist_path):
                os.remove(hls_playlist_path)

            # Delete only the .ts segments related to this specific video
            hls_dir = os.path.dirname(hls_playlist_path)  # Get the directory where the HLS files are stored

            for filename in os.listdir(hls_dir):
                os.remove(os.path.join(hls_dir, filename))
            if os.path.exists(hls_dir):
                os.rmdir(hls_dir)
        else:
            # If there is an empty directory, delete it
            try:
                video_dir = os.path.join(settings.MEDIA_ROOT, f'videos/hls_output/{self.id}')
                print('video_dir', video_dir)
                if os.path.exists(video_dir):
                    os.rmdir(video_dir)
            except Exception as e:
                print(e)
                print('There was an error deleting that directory or it never existed.')
        
        super().delete()
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)  # Save before invoking task

    @property
    def get_duration(self):
        # Check if duration is set and is not empty
        if self.duration:
            try:
                # Convert the duration to a float (seconds)
                seconds = float(self.duration)
                
                # Round the duration to the nearest minute
                minutes = math.ceil(seconds / 60)

                # Calculate hours and minutes
                hours = minutes // 60
                minutes = minutes % 60

                # Format as "Xhr Ymin"
                time_str = f"{hours}hr {minutes}min" if hours > 0 else f"{minutes}min"
                return time_str

            except ValueError:
                return "Invalid duration format"
        else:
            return "No duration available"

@receiver(pre_save, sender=Video)
def delete_old_video_on_change(sender, instance, **kwargs):
    if not instance.pk:
        # No primary key yet → it's a new object, nothing to delete
        return

    try:
        old_instance = Video.objects.get(pk=instance.pk)
    except Video.DoesNotExist:
        return

    old_file = old_instance.video
    new_file = instance.video

    # Only delete if:
    # 1. There was an old file
    # 2. The new file is different from the old file
    if old_file and old_file != new_file:
        old_path = old_file.path
        if os.path.isfile(old_path):
            try:
                os.remove(old_path)
                print(f"Deleted old video: {old_path}")
            except Exception as e:
                instance.errors = str(e)

@receiver(pre_save, sender=Video)
def video_presave(sender, instance, **kwargs):
    # --- slug handling ---
    if not instance.slug:
        instance.slug = slugify(instance.name or "")
    original_slug = instance.slug
    qs = Video.objects.filter(slug=instance.slug)
    if instance.pk:
        qs = qs.exclude(pk=instance.pk)
    counter = 1
    while qs.exists():
        instance.slug = f"{original_slug}-{counter}"
        counter += 1
        qs = Video.objects.filter(slug=instance.slug)
        if instance.pk:
            qs = qs.exclude(pk=instance.pk)

    # --- detect file change ---
    instance._video_changed = False
    if instance.pk:
        try:
            old = Video.objects.get(pk=instance.pk)
        except Video.DoesNotExist:
            old = None
        if old:
            # If the underlying file changed, mark for reprocess
            if old.video and instance.video and old.video.name != instance.video.name:
                instance._video_changed = True
            # If it was empty before and now has a file, that’s also a change
            elif (not old.video) and instance.video:
                instance._video_changed = True
    else:
        # New object with a file → will process after save
        if instance.video:
            instance._video_changed = True

    # If file changed (new upload), reset processing fields so a new run can happen
    if instance._video_changed:
        instance.status = 'Pending'
        instance.is_running = False
        instance.hls = None
        instance.errors = None

@receiver(post_save, sender=Video)
def trigger_video_processing(sender, instance, created, **kwargs):
    # Conditions under which we want to enqueue:
    should_queue = (
        created
        or getattr(instance, "_video_changed", False)
        or instance.status in ('Pending', 'Needs Reencode')
    )

    if should_queue and not instance.is_running:
        # Defer celery until DB commit to avoid races
        from content.tasks import process_video
        transaction.on_commit(lambda: process_video.delay(instance.id))
