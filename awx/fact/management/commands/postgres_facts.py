
# Python
import json
import sys
import os
from optparse import make_option
from datetime import timedelta

# awx
from fact.models import Fact, Host

# Django
import django
from django.utils import timezone
from django.conf import settings
from django.core.management.base import CommandError, BaseCommand
from django.db import connection


class WorkloadGenerator(object):
    params = {
        'hosts_total': 10000,
        'scans_total': 1095,
        'entropy_daily': 0.02,
        'entropy_yearly': 0.25,
        'start_date': None,
        'now': timezone.now(),
        'module_names': ['packages', 'ansible', 'services']
    }
    host_ids = [] 
    facts = {}

    def __init__(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        for module_name in self.params['module_names']:
            with open('%s/%s.json' % (current_dir, module_name)) as f:
                self.facts[module_name] = json.load(f)

    def create_hosts(self):
        host_objs = []
        for i in range(0, self.params['hosts_total']):
            host_objs.append(Host(name='host-%s' % (i+1)))
        Host.objects.bulk_create(host_objs)
        self.host_ids = Host.objects.all().values_list('id', flat=True).order_by('id')

    def generate(self):
        if not self.params['start_date']:
            self.params['start_date'] = self.params['now'] - timedelta(days=self.params['scans_total'] + 30)
            print(self.params['start_date'])

        self.create_hosts()
        print("%s hosts created" % self.params['hosts_total'])
       
        timestamp_current = self.params['now']
        for scan_idx in range(0, self.params['scans_total']):
            fact_objs = []
            for host_id in self.host_ids:
                for module_name in self.params['module_names']:
                    fact_objs.append(Fact(host_id=host_id, timestamp=timestamp_current, module=module_name, facts=self.facts[module_name]))
             
            timestamp_current -= timedelta(days=1)
            Fact.objects.bulk_create(fact_objs)

            now_updated_seconds = (timezone.now() - self.params['now']).seconds
            now_updated_minutes, ignore = divmod(now_updated_seconds, 60)
            time_left_seconds = (now_updated_seconds / (scan_idx+1)) * (self.params['scans_total'] - scan_idx)
            time_left_minutes, ignore = divmod(time_left_seconds, 60)
            time_left_minutesss, ignore = divmod(0, 60)
            print("Created facts for day %s time passed %s (min) time left %s (min)" % (scan_idx, now_updated_minutes, time_left_minutes))
            sys.stdout.flush()

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--drop', dest='drop', action='store_true',
                    default=False, help='Drop collections before generating workload.'),  
        make_option('--dbsize', dest='dbsize', action='store_true',
                    default=False, help='Print the size of the db.'), 
        make_option('--generate_workload', dest='generate_workload', action='store_true',
            default=False, help='Create database entries for parameters'),
    )

    def handle(self, *args, **options):
        if options.get('drop'):
            #Fact.objects.all().delete()
            #Host.objects.all().delete()
            os.system("./manage.py flush --noinput")
            os.system("./manage.py makemigrations")
            os.system("./manage.py migrate")
            pass
        
        if options.get('generate_workload'):
            wg = WorkloadGenerator()
            wg.generate()


        if options.get('dbsize'):
            cursor = connection.cursor()
            cursor.execute("SELECT pg_size_pretty(pg_database_size('%s'))" % settings.DATABASES['default']['NAME'])
            row = cursor.fetchone()
            print("Database size: %s" % row)

