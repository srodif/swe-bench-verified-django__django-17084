#!/usr/bin/env python
"""Debug SQL generation."""

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

# Debug the SQL being generated
queryset = TestModel.objects.all()
queryset = queryset.aggregate(
    DJR_total=Sum("DJR"),
)
print("Simple aggregate SQL:", str(queryset))

# Now with window annotation first
queryset = TestModel.objects.all()
queryset = queryset.annotate(
    cumul_DJR=Coalesce(Window(Sum("DJR"), order_by=F("date").asc()), 0.0)
)
print("Window annotation SQL:", str(queryset.query))

# Check the aggregate SQL generation
from django.db import connection
from django.db.models.sql import Query
from django.db.models.sql.compiler import SQLCompiler

query = queryset.query.chain()
query.add_annotation(Sum("cumul_DJR"), "cumul_DJR_total")

compiler = query.get_compiler(using='default')
print("Aggregate SQL:", compiler.as_sql())