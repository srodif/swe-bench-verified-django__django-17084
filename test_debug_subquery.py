#!/usr/bin/env python
"""Test if subquery is triggered."""

import os
import sys
import django
from django.conf import settings

# Configure Django settings
settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    INSTALLED_APPS=[
        'django.contrib.contenttypes',
        'django.contrib.auth',
    ],
    USE_TZ=True,
    LOGGING={
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django.db.backends': {
                'handlers': ['console'],
                'level': 'DEBUG',
            }
        }
    }
)

django.setup()

from django.db import models
from django.db.models import Sum, F, Window, Q
from django.db.models.functions import Coalesce

# Define test model
class TestModel(models.Model):
    date = models.DateField()
    DJR = models.FloatField()
    
    class Meta:
        app_label = 'test'

# Create the table
from django.db import connection
with connection.schema_editor() as schema_editor:
    schema_editor.create_model(TestModel)

# Create test data
from datetime import date
TestModel.objects.create(date=date(2023, 1, 1), DJR=10.0)
TestModel.objects.create(date=date(2023, 1, 2), DJR=20.0)
TestModel.objects.create(date=date(2023, 1, 3), DJR=30.0)

print("Testing aggregate over window functions...")

try:
    queryset = TestModel.objects.all()
    queryset = queryset.annotate(
        cumul_DJR=Coalesce(Window(Sum("DJR"), order_by=F("date").asc()), 0.0)
    )
    
    print("About to call aggregate...")
    aggregate = queryset.aggregate(
        DJR_total=Sum("DJR"),
        cumul_DJR_total=Sum("cumul_DJR")
    )
    print("Aggregate result:", aggregate)
    
except Exception as e:
    print("Error occurred:", type(e).__name__, str(e))