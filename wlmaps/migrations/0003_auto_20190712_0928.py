# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2019-07-12 09:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wlmaps', '0002_auto_20181119_1855'),
    ]

    operations = [
        migrations.AddField(
            model_name='map',
            name='wl_version_after',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='WL version after'),
        ),
        migrations.AlterField(
            model_name='map',
            name='descr',
            field=models.TextField(verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='map',
            name='file',
            field=models.FileField(upload_to='wlmaps/maps', verbose_name='Mapfile'),
        ),
        migrations.AlterField(
            model_name='map',
            name='h',
            field=models.PositiveIntegerField(verbose_name='Height'),
        ),
        migrations.AlterField(
            model_name='map',
            name='hint',
            field=models.TextField(blank=True, verbose_name='Hint'),
        ),
        migrations.AlterField(
            model_name='map',
            name='minimap',
            field=models.ImageField(upload_to='wlmaps/minimaps', verbose_name='Minimap'),
        ),
        migrations.AlterField(
            model_name='map',
            name='nr_downloads',
            field=models.PositiveIntegerField(default=0, verbose_name='Download count'),
        ),
        migrations.AlterField(
            model_name='map',
            name='nr_players',
            field=models.PositiveIntegerField(verbose_name='Max Players'),
        ),
        migrations.AlterField(
            model_name='map',
            name='uploader_comment',
            field=models.TextField(blank=True, verbose_name='Uploader comment'),
        ),
        migrations.AlterField(
            model_name='map',
            name='w',
            field=models.PositiveIntegerField(verbose_name='Width'),
        ),
    ]
