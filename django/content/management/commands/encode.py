from django.conf import settings
import subprocess
import os
import json
from django.core.management.base import BaseCommand, CommandError
from content.models import Video
from home.settings import MEDIA_ROOT

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

class Command(BaseCommand):
    help = 'Optimize Video (HLS) — mirrors Celery fast-path logic'

    def handle(self, *args, **kwargs):
        obj = None
        try:
            # Match Celery: pick first Pending
            obj = Video.objects.filter(status='Pending').first()
            if not obj:
                print('No video with status "Pending" found.')
                return

            # Reset errors and mark running (same as Celery)
            obj.errors = None
            obj.status = 'Processing'
            obj.is_running = True
            obj.save(update_fields=["errors", "status", "is_running"])

            # Paths
            input_video_rel_path = obj.video.name
            input_video_path = os.path.join(MEDIA_ROOT, input_video_rel_path)

            # Probe duration (same as Celery)
            try:
                probe = subprocess.run(
                    ["ffprobe", "-v", "quiet", "-print_format", "json",
                     "-show_format", "-show_streams", input_video_path],
                    check=True, stdout=subprocess.PIPE
                )
                meta = json.loads(probe.stdout)
                duration = None
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

            # Decide pipeline based on video codec (same as Celery)
            codec_raw = get_video_codec(input_video_path)   # e.g. "h264"
            codec = (codec_raw or "").strip().lower()
            print(f"Video title: {obj.name}")
            print(f"Video codec: {codec or 'unknown'}")

            if codec == "h264":
                # Build output paths only when we will actually encode
                output_directory_rel = os.path.join(os.path.dirname(input_video_rel_path), f'hls_output/{obj.id}')
                output_directory_abs = os.path.join(MEDIA_ROOT, output_directory_rel)
                os.makedirs(output_directory_abs, exist_ok=True)

                base_name = os.path.splitext(os.path.basename(input_video_rel_path))[0]
                output_filename = base_name + '_hls.m3u8'
                output_hls_rel_path = os.path.join(output_directory_rel, output_filename)
                output_hls_path = os.path.join(MEDIA_ROOT, output_hls_rel_path)

                output_thumbnail_rel_path = os.path.join(output_directory_rel, base_name + 'thumbnail.jpg')
                output_thumbnail_path = os.path.join(MEDIA_ROOT, output_thumbnail_rel_path)

                # ✅ Fast path: copy H.264 video (TS via annexb), AAC stereo
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

                # Finalize (same as Celery)
                obj.hls = output_hls_rel_path
                obj.status = 'Completed'
                obj.is_running = False
                obj.save()
                print(f'HLS segments generated and saved at: {output_hls_rel_path}')
            else:
                # ❌ Not supported by the fast path – mirror Celery's failure path
                msg = (
                    f"Unsupported codec for fast HLS path: '{codec or 'unknown'}'. "
                    "Re-encode to H.264 (or add a fallback that re-encodes)."
                )
                print(msg)
                obj.status = 'Failed'
                obj.is_running = False
                obj.errors = msg
                obj.save(update_fields=["status", "is_running", "errors"])
                return

        except Exception as e:
            # Mirror Celery error handling
            if obj:
                try:
                    obj.errors = str(e)
                    obj.is_running = False
                    obj.status = 'Failed'
                    obj.save(update_fields=["errors", "is_running", "status"])
                except Exception:
                    pass
            raise CommandError(e)
