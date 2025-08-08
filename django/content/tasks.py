from celery import shared_task
from .models import Video
import os
import subprocess
import json
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

MEDIA_ROOT = settings.MEDIA_ROOT

def get_video_codec(path: str) -> str:
    """Return codec_name of the first video stream, or '' if unknown."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=codec_name",
                "-of", "default=nw=1:nk=1",
                path
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[ffprobe] failed: {e.stderr or e}")
        return ""

@shared_task
def process_video(video_id):
    try:
        # Use the video_id we were passed
        obj = Video.objects.filter(pk=video_id, status='Pending').first()
        if not obj:
            error = f'No video with id={video_id} and status="Pending" found.'
            print(error)
            obj.errors = error
            obj.status = 'Failed'
            obj.save()
            return
        obj.errors = None
        obj.status = 'Processing'
        obj.is_running = True
        obj.save()

        # Input/output paths
        input_video_rel_path = obj.video.name  # relative to MEDIA_ROOT
        input_video_path = os.path.join(MEDIA_ROOT, input_video_rel_path)

        # Probe duration (fallback to format duration if stream duration missing)
        try:
            probe = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", input_video_path],
                check=True, stdout=subprocess.PIPE
            )
            meta = json.loads(probe.stdout)
            duration = None
            # prefer format.duration
            if "format" in meta and "duration" in meta["format"]:
                duration = float(meta["format"]["duration"])
            else:
                for s in meta.get("streams", []):
                    if s.get("codec_type") == "video" and "duration" in s:
                        duration = float(s["duration"])
                        break
            if duration:
                obj.duration = duration
                obj.save(update_fields=["duration"])
        except Exception as e:
            print(f"[ffprobe] duration probe failed: {e}")

        # Decide pipeline based on video codec
        # codec_type = get_video_codec(input_video_path)
        # video_title = f"Video title: {obj.name}"
        # codec_type = f"Video codec: {codec_type or 'unknown'}"
        # Decide pipeline based on video codec
        codec_raw = get_video_codec(input_video_path)          # e.g. "h264"
        codec = (codec_raw or "").strip().lower()              # normalize
        print(f"Video title: {obj.name}")
        print(f"Video codec: {codec or 'unknown'}")

        if codec == "h264":
            output_directory_rel = os.path.join(os.path.dirname(input_video_rel_path), f'hls_output/{obj.id}')
            output_directory_abs = os.path.join(MEDIA_ROOT, output_directory_rel)
            os.makedirs(output_directory_abs, exist_ok=True)

            base_name = os.path.splitext(os.path.basename(input_video_rel_path))[0]
            output_filename = base_name + '_hls.m3u8'
            output_hls_rel_path = os.path.join(output_directory_rel, output_filename)
            output_hls_path = os.path.join(MEDIA_ROOT, output_hls_rel_path)

            output_thumbnail_rel_path = os.path.join(output_directory_rel, base_name + 'thumbnail.jpg')
            output_thumbnail_path = os.path.join(MEDIA_ROOT, output_thumbnail_rel_path)
            # ✅ Fast path: copy H.264 video (TS-friendly via annexb), transcode audio to AAC-LC stereo
            cmd = [
                'ffmpeg', '-i', input_video_path,
                '-map', '0:v:0', '-map', '0:a:0?', '-sn',
                '-c:v', 'copy', '-bsf:v', 'h264_mp4toannexb',
                '-c:a', 'aac', '-b:a', '128k', '-ac', '2', '-ar', '48000',
                '-hls_time', '6',
                '-hls_flags', 'independent_segments',
                '-hls_list_size', '0',
                '-hls_playlist_type', 'vod',
                '-hls_base_url', '{{ dynamic_path }}/',
                '-f', 'hls',
                output_hls_path,
            ]
            subprocess.run(cmd, check=True)

            # Generate thumbnail only if missing
            if not obj.thumbnail:
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
                obj.thumbnail = output_thumbnail_rel_path  # store relative path

            # Finalize
            obj.hls = output_hls_rel_path
            obj.status = 'Completed'
            obj.is_running = False
            obj.save()
            print(f'HLS segments generated and saved at: {output_hls_rel_path}')
        else:
            # ❌ Not supported by the fast path – don’t produce a broken HLS
            msg = (
                f"Unsupported codec for fast HLS path: '{codec or 'unknown'}'. "
                "Re-encode to H.264 (or add a fallback that re-encodes)."
            )
            print(msg)
            obj.status = 'Failed'
            obj.is_running = False
            obj.errors = msg
            obj.save()
            return

    except Exception as e:
        # Ensure flags reset on error
        try:
            obj.errors = e
            obj.is_running = False
            obj.status = 'Failed'
            obj.save(update_fields=["is_running", "status"])
        except Exception:
            pass
        raise CommandError(e)
