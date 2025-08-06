import os
import math
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from django.db.models.signals import pre_save
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
    
    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
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
    is_running = models.BooleanField(default=False)
  
    # ✅ New fields
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
def video_presave(sender, instance, **kwargs):
    if not instance.slug:  # Generate slug if not already set
        instance.slug = slugify(instance.name)
    
    # Ensure the slug is unique
    original_slug = instance.slug
    queryset = Video.objects.filter(slug=instance.slug)
    
    # Exclude the current instance in case it's an update
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    
    count = 1
    while queryset.exists():
        instance.slug = f"{original_slug}-{count}"
        count += 1
        queryset = Video.objects.filter(slug=instance.slug)
        if instance.pk:
            queryset = queryset.exclude(pk=instance.pk)

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Video)
def trigger_video_processing(sender, instance, created, **kwargs):
    if created:  # Only process new videos
        from content.tasks import process_video
        process_video.delay(instance.id)
