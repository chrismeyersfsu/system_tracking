# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fact', '0003_auto_20160205_1530'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fact',
            name='module',
            field=models.CharField(max_length=128, db_index=True),
        ),
        migrations.AlterField(
            model_name='fact',
            name='timestamp',
            field=models.DateTimeField(default=None, editable=False, db_index=True),
        ),
    ]
