from django.core.management.base import BaseCommand
from django.core.files import File
from content.models import Video
import os

class Command(BaseCommand):
    help = 'Assign an existing video file to the database'

    def add_arguments(self, parser):
        parser.add_argument('video_path', type=str)
        parser.add_argument('name', type=str)
        parser.add_argument('description', type=str)

    def handle(self, *args, **kwargs):
        video_path = kwargs['video_path']
        name = kwargs['name']
        description = kwargs['description']

        if not os.path.exists(video_path):
            self.stdout.write(self.style.ERROR(f"File does not exist: {video_path}"))
            return

        with open(video_path, 'rb') as f:
            video_instance = Video(
                name=name,
                description=description,
                video=File(f, name=os.path.basename(video_path)),
                status=Video.PENDING
            )
            video_instance.save()

        self.stdout.write(self.style.SUCCESS(f"Video '{name}' assigned successfully!"))
