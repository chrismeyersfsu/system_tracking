from django.db import models
from jsonbfield.fields import JSONField

class Host(models.Model):
    name = models.CharField(max_length=512, unique=True)

class Fact(models.Model):
    """A model representing a fact returned from Ansible.
    Facts are stored as JSON dictionaries, individually if at all possible.
    """
    host = models.ForeignKey(Host)
    timestamp = models.DateTimeField(default=None, editable=False)
    created = models.DateTimeField(editable=False, auto_now_add=True)
    modified = models.DateTimeField(editable=False, auto_now=True)
    module = models.CharField(max_length=128)
    facts = JSONField(blank=True, default={})

    index_together = [
        ["timestamp", "module", "host"],
    ]

