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

load_dotenv()


def root_view(request):
    return HttpResponse("Hello! You're at the root of the BeanHub server.")


urlpatterns = [
    path(env('DJANGO_DEBUG_URL'), include("debug_toolbar.urls")),
    path(env('DJANGO_ADMIN_URL'), admin.site.urls),
    path(env('DJANGO_ROOT_URL'), root_view, name='root'),
    path(env('DJANGO_AUDIO_ENDPOINT_URL'), include('src.audio_endpoint.urls')),
]
