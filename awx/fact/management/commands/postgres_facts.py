
# Python
import json
import sys
import os
import random
import math
from optparse import make_option
from datetime import timedelta
from datetime import datetime

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

class Stats(object):
    runs = 0
    avg = 0
    stdev = 0
    min = 0
    max = 0

    def __init__(self, time_diffs):
        total = 0
        count = len(time_diffs)
        max_delta = time_diffs[0]
        min_delta = time_diffs[0]
        for diff in time_diffs:
            total += diff.total_seconds()
            if diff < min_delta:
                min_delta = diff
            if diff > max_delta:
                max_delta = diff

        avg = total / count

        std_total = 0
        for diff in time_diffs:
            std_total += pow((diff.total_seconds() - avg), 2)
        std_avg = std_total / count

        std = math.sqrt(std_avg)

        self.runs = count
        self.avg = avg
        self.stdev = std
        self.max = max_delta.total_seconds()
        self.min = min_delta.total_seconds()

    def print_stats(self):
        print("RUNS: %s" % self.runs)
        print("AVG: %s s" % self.avg)
        print("STDEV: %s s" % self.stdev)
        print("MAX: %s s" % self.max)
        print("MIN: %s s" % self.min) 
        sys.stdout.flush()

class Experiment(object):
    module_names = ['ansible', 'services', 'packaging']

    def __init__(self):
        self.hosts = Host.objects.all()
        self.hosts_len = Host.objects.all().count()
        self.host_ids = Host.objects.all().values_list('id', flat=True)
        self.host_ids_len = len(self.host_ids)
        self.scan_timestamps = Fact.objects.filter(host__id=self.hosts[0].id).values_list('timestamp', flat=True)
        self.scan_timestamps_len = len(self.scan_timestamps)
        self.scan_timestamp_begin = Fact.objects.filter(host__id=self.hosts[0].id).values_list('timestamp', flat=True).order_by('timestamp')[0]
        self.scan_timestamp_end = Fact.objects.filter(host__id=self.hosts[0].id).values_list('timestamp', flat=True).order_by('-timestamp')[0]
        self.scan_timestamp_diff = self.scan_timestamp_end - self.scan_timestamp_begin

    def get_rand_scan_timestamp(self):
        return self.scan_timestamps[random.randint(0, self.scan_timestamps_len-1)]

    '''
    Generate a timestamp within the range of the first timestamp to the last.
    '''
    def generate_rand_timestamp(self):
        diff_sec = self.scan_timestamp_diff.total_seconds()
        rand_time_sec = random.randint(0, diff_sec)
        return self.scan_timestamp_end - timedelta(seconds=rand_time_sec)
        

    def get_rand_host(self):
        return self.hosts[random.randint(0, self.hosts_len-1)]

    def run_timeline(self, runs, module_name='ansible'):
        time_diffs = []
        for i in xrange(0, runs):
            rand_host = self.get_rand_host()
            time_before = datetime.now()
            results = Fact.objects.filter(host__id=rand_host.id, module=module_name).values_list('timestamp', flat=True).distinct('timestamp')
            list(results)
            time_after = datetime.now()
            time_diffs.append(time_after - time_before)

        return Stats(time_diffs)

    def run_host_facts(self, runs, module_name='ansible'):
        time_diffs = []
        for i in xrange(0, runs):
            rand_host = self.get_rand_host()
            rand_scan_timestamp = self.generate_rand_timestamp()
            time_before = datetime.now()
            results = Fact.objects.filter(host__id=rand_host.id, module=module_name, timestamp__lte=rand_scan_timestamp).order_by('timestamp')
            list(results)
            time_after = datetime.now()
            time_diffs.append(time_after - time_before)
        
        return Stats(time_diffs)

    def run_single_fact(self, runs, module_name='ansible'):
        time_diffs = []
        for i in xrange(0, runs):
            rand_scan_timestamp = self.generate_rand_timestamp()
            time_before = datetime.now()
            results = Fact.objects.filter(host__id__in=self.host_ids, module=module_name, timestamp__lte=rand_scan_timestamp).order_by('host__id', '-timestamp').distinct('host__id')
            list(results)
            time_after = datetime.now()
            time_diffs.append(time_after - time_before)

        return Stats(time_diffs)

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--drop', dest='drop', action='store_true',
                    default=False, help='Drop collections before generating workload.'),  
        make_option('--dbsize', dest='dbsize', action='store_true',
                    default=False, help='Print the size of the db.'), 
        make_option('--generate_workload', dest='generate_workload', action='store_true',
            default=False, help='Create database entries for parameters'),
        make_option('--experiment_timeline', dest='experiment_timeline', action='store_true',
            default=False, help='Perform timeline experiment for a single host'),
        make_option('--experiment_host_facts', dest='experiment_host_facts', action='store_true',
            default=False, help='Perform experiment that exercises single set of facts for a point in time for a single host.'),
        make_option('--experiment_single_fact', dest='experiment_single_fact', action='store_true',
            default=False, help='Perform experiment that exercises getting a single fact across all hosts for a single point in time.'),
    )

    def handle(self, *args, **options):
        runs = 20
        if options.get('drop'):
            #Fact.objects.all().delete()
            #Host.objects.all().delete()
            os.system("./manage.py flush --noinput")
            os.system("./manage.py makemigrations")
            os.system("./manage.py migrate")
        
        if options.get('generate_workload'):
            wg = WorkloadGenerator()
            wg.generate()
            print("Finished generating workload!")

        if options.get('dbsize'):
            cursor = connection.cursor()
            cursor.execute("SELECT pg_size_pretty(pg_database_size('%s'))" % settings.DATABASES['default']['NAME'])
            row = cursor.fetchone()
            print("Database size: %s" % row)

        if options.get('experiment_timeline'):
            Exp = Experiment()
            stats = Exp.run_timeline(runs)
            print("Timeline Experiment Results:")
            stats.print_stats()
            print("")

        if options.get('experiment_host_facts'):
            Exp = Experiment()
            stats = Exp.run_host_facts(runs)
            print("Host Fact in Time Results:")
            stats.print_stats()
            print("")

        if options.get('experiment_single_fact'):
            Exp = Experiment()
            stats = Exp.run_single_fact(runs)
            print("Single Fact All Hosts Time Results:")
            stats.print_stats()
            print("")
