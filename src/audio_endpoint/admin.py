from django.contrib import admin
from .models import AudioFile


@admin.register(AudioFile)
class AudioAdmin(admin.ModelAdmin):
    list_display = ['file_path', 'unique_id', 'json_order']