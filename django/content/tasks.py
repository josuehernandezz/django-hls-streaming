from celery import shared_task
from .models import Video
import os
import subprocess
import json
from django.conf import settings

@shared_task
def process_video(video_id):
    try:
        obj = Video.objects.get(id=video_id)

        obj.status = 'Processing'
        obj.is_running = True
        obj.save()

        input_video_rel_path = obj.video.name  # Relative path within MEDIA_ROOT
        input_video_path = os.path.join(settings.MEDIA_ROOT, input_video_rel_path)

        output_directory_rel = os.path.join(os.path.dirname(input_video_rel_path), f'hls_output/{obj.id}')
        output_directory_abs = os.path.join(settings.MEDIA_ROOT, output_directory_rel)
        os.makedirs(output_directory_abs, exist_ok=True)

        output_filename = os.path.splitext(os.path.basename(input_video_rel_path))[0] + '_hls.m3u8'
        output_hls_rel_path = os.path.join(output_directory_rel, output_filename)
        output_hls_path = os.path.join(settings.MEDIA_ROOT, output_hls_rel_path)

        output_thumbnail_rel_path = os.path.join(output_directory_rel, os.path.splitext(os.path.basename(input_video_rel_path))[0]+'thumbnail.jpg')
        output_thumbnail_path = os.path.join(settings.MEDIA_ROOT, output_thumbnail_rel_path)

        # Get video duration
        command = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            input_video_path
        ]
        result = subprocess.run(command, shell=False, check=True, stdout=subprocess.PIPE)
        output_json = json.loads(result.stdout)

        video_length = None
        for stream in output_json['streams']:
            if stream['codec_type'] == 'video':
                video_length = float(stream['duration'])
                break

        if video_length is not None:
            obj.duration = video_length

        # Create HLS segments
        cmd = [
            'ffmpeg', 
            '-i', input_video_path,
            '-codec', 'copy',
            '-hls_time', '10',
            '-hls_flags', 'independent_segments',
            '-hls_list_size', '0',
            '-f', 'hls',
            "-hls_base_url", "{{ dynamic_path }}/",
            output_hls_path
        ]
        subprocess.run(cmd, check=True)

        # Generate thumbnail
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', input_video_path,
            '-ss', '2',
            '-vframes', '1',
            '-q:v', '2',
            '-y',
            output_thumbnail_path
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        obj.hls = output_hls_rel_path
        obj.thumbnail = output_thumbnail_rel_path
        obj.status = 'Completed'
        obj.is_running = False
        obj.save()

    except Exception as e:
        obj.status = 'Failed'
        obj.is_running = False
        obj.save()
        raise e
