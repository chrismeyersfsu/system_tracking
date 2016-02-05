# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fact', '0001_initial'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='fact',
            index_together=set([('timestamp', 'module', 'host')]),
        ),
    ]
