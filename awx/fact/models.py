from django.db import models
from jsonbfield.fields import JSONField

class Host(models.Model):
    name = models.CharField(max_length=512, unique=True)

class Fact(models.Model):
    """A model representing a fact returned from Ansible.
    Facts are stored as JSON dictionaries, individually if at all possible.
    """
    host = models.ForeignKey(Host, db_index=True)
    timestamp = models.DateTimeField(default=None, editable=False, db_index=True)
    created = models.DateTimeField(editable=False, auto_now_add=True)
    modified = models.DateTimeField(editable=False, auto_now=True)
    module = models.CharField(max_length=128, db_index=True)
    facts = JSONField(blank=True, default={})

    class Meta:
    	index_together = [
        	["timestamp", "module", "host"],
        	["timestamp", "module"],
    	]

