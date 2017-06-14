# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-06-14 23:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academic', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='course',
            name='id',
        ),
        migrations.RemoveField(
            model_name='discipline',
            name='id',
        ),
        migrations.RemoveField(
            model_name='faculty',
            name='id',
        ),
        migrations.AlterField(
            model_name='course',
            name='slug',
            field=models.SlugField(help_text='Unique short name used on urls.', primary_key=True, serialize=False, verbose_name='Short name'),
        ),
        migrations.AlterField(
            model_name='discipline',
            name='slug',
            field=models.SlugField(help_text='Unique short name used on urls.', primary_key=True, serialize=False, verbose_name='Short name'),
        ),
        migrations.AlterField(
            model_name='faculty',
            name='slug',
            field=models.SlugField(help_text='Unique short name used on urls.', primary_key=True, serialize=False, verbose_name='Short name'),
        ),
    ]
