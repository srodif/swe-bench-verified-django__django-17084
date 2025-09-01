#!/usr/bin/env python
"""Debug script to understand the issue better."""

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

# Debug the annotations
queryset = TestModel.objects.all()
queryset = queryset.annotate(
    cumul_DJR=Coalesce(Window(Sum("DJR"), order_by=F("date").asc()), 0.0)
)

# Let's check the annotation properties
for annotation in queryset.query.annotations.values():
    print(f"Annotation: {annotation}")
    print(f"  Type: {type(annotation)}")
    print(f"  contains_aggregate: {getattr(annotation, 'contains_aggregate', 'Not found')}")
    print(f"  contains_over_clause: {getattr(annotation, 'contains_over_clause', 'Not found')}")
    if hasattr(annotation, 'source_expression'):
        print(f"  source_expression: {annotation.source_expression}")
        print(f"  source_expression.contains_aggregate: {getattr(annotation.source_expression, 'contains_aggregate', 'Not found')}")
        print(f"  source_expression.contains_over_clause: {getattr(annotation.source_expression, 'contains_over_clause', 'Not found')}")
        
print("\n" + "="*50)
print("Raw query:", str(queryset.query))

# Test the aggregate
aggregate = queryset.aggregate(
    DJR_total=Sum("DJR"),
    cumul_DJR_total=Sum("cumul_DJR")
)