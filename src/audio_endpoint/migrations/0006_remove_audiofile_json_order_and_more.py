# Generated by Django 5.0 on 2024-01-07 18:56
# pylint: disable=all
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("audio_endpoint", "0005_rename_file_audiofile_file_path_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="audiofile",
            name="json_order",
        ),
        migrations.RemoveField(
            model_name="audiofile",
            name="unique_id",
        ),
    ]
