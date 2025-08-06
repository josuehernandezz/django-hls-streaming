from django.conf import settings

def global_project_context(request):
    return {
        "PROJECT_NAME": settings.PROJECT_NAME,
        "PROJECT_YEAR": settings.PROJECT_YEAR,
    }
