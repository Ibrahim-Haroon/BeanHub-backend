from django.contrib import admin
from .models import AudioFile


@admin.register(AudioFile)
class AudioAdmin(admin.ModelAdmin):
    list_display = ['display_audio', 'floating_point_number']

    def display_audio(self, obj):
        return obj.file.url if obj.file else None

    display_audio.short_description = 'Audio File'
