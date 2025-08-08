from celery import shared_task
from .models import Video
import os
import subprocess
import json
from pathlib import Path
from django.conf import settings
from django.core.management.base import CommandError
from django.utils.text import slugify
from .utils import resolve_input_path  # make sure this exists

MEDIA_ROOT = settings.MEDIA_ROOT

def get_video_codec(path: str) -> str:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error",
             "-select_streams", "v:0",
             "-show_entries", "stream=codec_name",
             "-of", "default=nw=1:nk=1",
             path],
            capture_output=True, text=True, check=True,
        )
        return r.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[ffprobe] failed: {e.stderr or e}")
        return ""

@shared_task
def process_video(video_id):
    obj = None
    try:
        obj = Video.objects.filter(pk=video_id, status='Pending').first()
        if not obj:
            # Nothing to do; surface a clear message on the record if it exists.
            maybe = Video.objects.filter(pk=video_id).first()
            if maybe:
                msg = f'Video id={video_id} is not Pending (status={maybe.status}).'
                print(msg)
                maybe.errors = msg
                maybe.status = 'Failed'
                maybe.save(update_fields=["errors", "status"])
            else:
                print(f'No video with id={video_id} found.')
            return

        obj.errors = None
        obj.status = 'Processing'
        obj.is_running = True
        obj.save(update_fields=["errors", "status", "is_running"])

        # --- INPUT PATH (upload or server path) ---
        input_video_path = resolve_input_path(obj)  # absolute path        
        src_stem = Path(input_video_path).stem
        safe_base = slugify(src_stem) or f"video_{obj.id}"

        # --- DURATION PROBE ---
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
                        duration = float(s["duration"]); break
            if duration:
                obj.duration = duration
                obj.save(update_fields=["duration"])
        except Exception as e:
            print(f"[ffprobe] duration probe failed: {e}")

        # --- CODEC DECISION ---
        codec = (get_video_codec(input_video_path) or "").strip().lower()
        # print(f"Video title: {obj.name}")
        # print(f"Video codec: {codec or 'unknown'}")

        if codec != "h264":
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

        # --- OUTPUT PATHS (always under MEDIA_ROOT/hls_output/<id>/) ---
        output_dir_rel = os.path.join("videos/hls_output", str(obj.id))
        # print('output_dir_rel', output_dir_rel)
        output_dir_abs = os.path.join(MEDIA_ROOT, output_dir_rel)
        # print('output_dir_abs', output_dir_abs)
        os.makedirs(output_dir_abs, exist_ok=True)

        m3u8_name = f"{safe_base}_hls.m3u8"
        seg_pattern = f"{safe_base}_hls%03d.ts"

        output_hls_rel_path = os.path.join(output_dir_rel, m3u8_name)
        output_hls_path = os.path.join(MEDIA_ROOT, output_hls_rel_path)

        # Thumbnail next to the playlist
        thumb_name = f"{safe_base}_thumb.jpg"
        output_thumbnail_rel_path = os.path.join(output_dir_rel, thumb_name)
        output_thumbnail_path = os.path.join(MEDIA_ROOT, output_thumbnail_rel_path)

        # --- FFMPEG: copy H.264 video to Annex B, transcode audio to AAC stereo ---
        cmd = [
            'ffmpeg', '-i', input_video_path,
            '-map', '0:v:0', '-map', '0:a:0?', '-sn',
            '-c:v', 'copy', '-bsf:v', 'h264_mp4toannexb',
            '-c:a', 'aac', '-b:a', '128k', '-ac', '2', '-ar', '48000',
            '-hls_time', '6',
            '-hls_flags', 'independent_segments',
            '-hls_list_size', '0',
            '-hls_playlist_type', 'vod',
            '-hls_segment_filename', os.path.join(output_dir_abs, seg_pattern),
            '-hls_base_url', '{{ dynamic_path }}/',
            '-f', 'hls', output_hls_path,
        ]
        subprocess.run(cmd, check=True)

        # --- THUMBNAIL (only if missing) ---
        if not obj.thumbnail:
            thumb_cmd = [
                'ffmpeg', '-i', input_video_path,
                '-ss', '2', '-vframes', '1', '-q:v', '2', '-y',
                output_thumbnail_path
            ]
            subprocess.run(thumb_cmd, check=True)
            obj.thumbnail = output_thumbnail_rel_path

        # --- FINALIZE ---
        obj.hls = output_hls_rel_path
        obj.status = 'Completed'
        obj.is_running = False
        obj.save(update_fields=["hls", "thumbnail", "status", "is_running"])
        print(f'HLS segments generated at: {output_hls_rel_path}')

    except Exception as e:
        # Ensure flags reset on error
        if obj:
            try:
                obj.errors = str(e)
                obj.is_running = False
                obj.status = 'Failed'
                obj.save(update_fields=["errors", "is_running", "status"])
            except Exception:
                pass
        raise CommandError(e)