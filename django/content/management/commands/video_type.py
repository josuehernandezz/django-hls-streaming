from django.conf import settings
import subprocess
import os
import json
from django.core.management.base import BaseCommand, CommandError
from content.models import Video
from home.settings import MEDIA_ROOT

class Command(BaseCommand):
    help = 'Optimize Video'

    def add_arguments(self, parser):
        parser.add_argument('video_id', type=str)

    def handle(self, *args, **kwargs):
        video_id = kwargs['video_id']

        try:
            obj = Video.objects.get(id=video_id)
            if obj:
                # Get the relative path from MEDIA_ROOT
                input_video_rel_path = obj.video.name  # Relative path within MEDIA_ROOT
                input_video_path = os.path.join(MEDIA_ROOT, input_video_rel_path)

                def get_video_codec(path):
                    result = subprocess.run(
                        [
                            "ffprobe", "-v", "error",
                            "-select_streams", "v:0",
                            "-show_entries", "stream=codec_name",
                            "-of", "default=nw=1:nk=1",
                            path
                        ],
                        capture_output=True,
                        text=True
                    )
                    return result.stdout.strip()
                codec = get_video_codec(input_video_path)
                print(f"Video title: {obj.name}")
                print(f"Video codec: {codec}")
            else:
                print('No video with status "Completed" found.')
        except Exception as e:
            raise CommandError(e)
