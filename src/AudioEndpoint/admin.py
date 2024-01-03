from django.contrib import admin
from .models import AudioFile

@admin.register(AudioFile)
class AudioAdmin(admin.ModelAdmin):
    list_display = ['audio_name', 'description', 'display_audio', 'created_at', 'updated_at']

    def display_audio(self, obj):
        return obj.file.url if obj.file else None

    display_audio.short_description = 'Audio File'
