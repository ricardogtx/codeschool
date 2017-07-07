# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-07-07 14:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.IntegerField(choices=[(0, 'Student'), (1, 'Teacher'), (2, 'School staff'), (3, 'Administrator')], default=0, help_text='User main role in the codeschool platform.', verbose_name='Role'),
        ),
    ]
