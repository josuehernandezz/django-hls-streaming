from django.templatetags.static import static
from django.utils.html import strip_tags
from django.urls import resolve
from content.models import Video
from django.conf import settings

def dynamic_og_context(request):
    path = request.path
    base_url = request.build_absolute_uri('/')

    # Default OG values
    og_title = settings.PROJECT_NAME + " | Stream Video Online"
    og_description = "Upload and stream your own content via adaptive HLS."
    og_image = request.build_absolute_uri(static('img/logo.jpg'))
    og_url = request.build_absolute_uri(path)

    # Check if this is a video detail view
    match = resolve(path)
    if match.url_name == 'movie':  # Adjust based on your actual URL name
        slug = match.kwargs.get('video_id')
        try:
            video = Video.objects.get(slug=slug)
            og_title = video.name
            og_description = strip_tags(video.description)[:200]
            if video.thumbnail:
                og_image = request.build_absolute_uri(video.thumbnail.url)
        except Video.DoesNotExist:
            pass

    return {
        'og_title': og_title,
        'og_description': og_description,
        'og_image': og_image,
        'og_url': og_url,
    }
