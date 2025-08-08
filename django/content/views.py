from django.shortcuts import render
from django.templatetags.static import static
# Create your views here.
from django.contrib.auth.decorators import login_required

import os 
from django.urls import reverse
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from .models import Video
from home.settings import MEDIA_ROOT
from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse


# @login_required
def home(request):
    return render(request, 'content/index.html', {'videos': Video.objects.filter(status='Completed')})

# @login_required
def movie_detail_view(request, video_id):
    video = Video.objects.filter(slug=video_id).first()
    hls_playlist_url = reverse('serve_hls_playlist', args=[video.id])

    context = {
        'hls_url': hls_playlist_url,
        'video': video,
    }
    return render(request, 'content/movie_detail.html', context)

# @login_required
def serve_hls_playlist(request, video_id):
    try:
        video = get_object_or_404(Video, pk=video_id)
        hls_playlist_path = MEDIA_ROOT / video.hls
        with open(hls_playlist_path, 'r') as m3u8_file:
            m3u8_content = m3u8_file.read()

        base_url = request.build_absolute_uri('/') 
        serve_hls_segment_url = base_url +"serve_hls_segment/" + str(video_id)
        m3u8_content = m3u8_content.replace('{{ dynamic_path }}', serve_hls_segment_url)

        return HttpResponse(m3u8_content, content_type='application/vnd.apple.mpegurl')
    except (Video.DoesNotExist, FileNotFoundError) as e:
        print(f"Error: {e}")
        return HttpResponse("Video or HLS playlist not found", status=404)

def serve_hls_segment(request, video_id, segment_name):
    video = get_object_or_404(Video, pk=video_id)

    # We expect video.hls to be a relative path under MEDIA_ROOT, like:
    #   hls_output/<id>/<name>_hls.m3u8
    if not video.hls:
        return HttpResponse("HLS playlist not generated yet.", status=404)

    playlist_abs = os.path.join(settings.MEDIA_ROOT, video.hls)
    hls_directory = os.path.dirname(playlist_abs)  # folder that contains the .ts files

    # Normalize/secure the requested segment path to prevent path traversal
    requested = os.path.normpath(os.path.join(hls_directory, segment_name))
    if not requested.startswith(os.path.abspath(hls_directory) + os.sep):
        return HttpResponse("Invalid segment path.", status=400)

    if not os.path.isfile(requested):
        raise Http404("Segment not found")

    # Serve with proper content-type and a bit of caching
    resp = FileResponse(open(requested, 'rb'), content_type='video/mp2t')
    resp['Cache-Control'] = 'public, max-age=300'
    resp['X-Content-Type-Options'] = 'nosniff'
    return resp

# @login_required
# def serve_hls_segment(request, video_id, segment_name):
#     try:
#         video = get_object_or_404(Video, pk=video_id)
#         try:
#             hls_directory = os.path.join(os.path.dirname(video.video.path), f'hls_output/{video.id}')
#         except:
#             hls_directory = os.path.join(os.path.dirname(video.video.path), f'hls_output/{video.id}')

#         segment_path = os.path.join(hls_directory, segment_name)

#         # Serve the HLS segment as a binary file response
#         return FileResponse(open(segment_path, 'rb'))
#     except (Video.DoesNotExist, FileNotFoundError):
#         return HttpResponse("Video or HLS segment not found", status=404)

