"""
URL configuration for django_beanhub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from os import getenv as env
from dotenv import load_dotenv
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

load_dotenv()


SchemaView = get_schema_view(
   openapi.Info(
      title="BeanHub API",
      default_version='v1',
      description="API documentation for the BeanHub project",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


# pylint: disable=W0613
def root_view(
        request
) -> HttpResponse:  # pragma: no cover
    """
    @rtype: HttpResponse
    @param request: request object
    @return: response for root view
    """
    return HttpResponse("Hello! You're at the root of the BeanHub server.")


urlpatterns = [
    path(env('DJANGO_DEBUG_URL', default='__debug__/'),
         include("debug_toolbar.urls")),
    path(env('DJANGO_ADMIN_URL', default="admin/"),
         admin.site.urls),
    path(env('DJANGO_ROOT_URL', default=''),
         root_view, name='root'),
    path(env('DJANGO_AUDIO_ENDPOINT_URL',
             default='audio_endpoint/'),
         include('src.audio_endpoint.urls')),
    path(env('DJANGO_AUDIO_STREAM_URL', default='audio_stream/'),
         include('src.audio_stream.urls')),
    path(env('DJANGO_SWAGGER_URL', default='swagger/'),
         SchemaView.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path(env('DJANGO_REDOC_URL', default='redoc/'),
         SchemaView.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
