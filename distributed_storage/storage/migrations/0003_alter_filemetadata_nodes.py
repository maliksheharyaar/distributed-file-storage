# Generated by Django 5.1.5 on 2025-03-16 00:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0002_filemetadata_file_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filemetadata',
            name='nodes',
            field=models.JSONField(default=list),
        ),
    ]
