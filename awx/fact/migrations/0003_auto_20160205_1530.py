# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fact', '0002_auto_20160205_1512'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='fact',
            index_together=set([('timestamp', 'module', 'host'), ('timestamp', 'module')]),
        ),
    ]
