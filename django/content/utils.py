# content/utils.py
import os
from pathlib import Path
from django.conf import settings

def resolve_input_path(video_obj) -> str:
    allowed = (getattr(settings, 'ALLOWED_IMPORT_DIRS', []) or [])
    if video_obj.source_type == 'server':
        raw = (video_obj.server_path or '').strip()
        if not raw:
            raise ValueError("Server-path mode requires 'server_path'.")
        # If it’s just a filename, assume it lives in the first allowed dir
        if os.sep not in raw and allowed:
            raw = str(Path(allowed[0]) / raw)
        real = Path(raw).expanduser().resolve()
        # must be inside an allowed dir
        ok = any(str(real).startswith(str(Path(b).expanduser().resolve()) + os.sep) or real == Path(b).expanduser().resolve()
                 for b in allowed)
        if not (ok and real.is_file()):
            raise ValueError("server_path is not a file inside an allowed import directory.")
        return str(real)

    # upload mode
    if not video_obj.video:
        raise ValueError("Upload mode selected but no file present.")
    return os.path.join(settings.MEDIA_ROOT, video_obj.video.name)
