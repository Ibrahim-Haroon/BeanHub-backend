from django.contrib import admin
from .models import AudioFile


@admin.register(AudioFile)
class AudioAdmin(admin.ModelAdmin):
    list_display = ['file_path', 'unique_id', 'json_order']
    readonly_fields = ['unique_id']
    search_fields = ['file_path', 'unique_id']
    list_filter = ['file_path', 'unique_id']

    def short_json_order(self, obj):
        return str(obj.json_order)[:50]  # Display the first 50 objects

    short_json_order.short_description = 'JSON Order (shortened)'
