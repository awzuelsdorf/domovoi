# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

import django_filters

class DomainActions(models.Model):
    name = models.TextField(primary_key=True, blank=False)
    domain = models.TextField(blank=False, null=False)
    first_time_seen = models.DateTimeField(blank=False, null=False, choices=((None, 'Yes Or No'), (True, 'Yes'), (False, 'No')))
    last_time_seen = models.DateTimeField(blank=False, null=False)
    permitted = models.BooleanField(blank=False, null=True, choices=((True, 'Yes'), (False, 'No')))
    reason = models.TextField(blank=False, null=False)

    class Meta:
        managed = False
        db_table = 'domain_actions'

class DomainActionsFilter(django_filters.FilterSet):
    class Meta:
        model = DomainActions

        fields = {
            'name': ['icontains'],
            'domain': ['icontains'],
            'reason': ['icontains'],
            'permitted': ['exact'],
            'last_time_seen': ['lte', 'gte'],
            'first_time_seen': ['lte', 'gte']
        }
