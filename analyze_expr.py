#!/usr/bin/env python
"""Analyze the resolved expression."""

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

print("Analyzing the expression resolution...")

queryset = TestModel.objects.all()
queryset = queryset.annotate(
    cumul_DJR=Coalesce(Window(Sum("DJR"), order_by=F("date").asc()), 0.0)
)

# Get the annotation
annotation = queryset.query.annotations['cumul_DJR']
print(f"Annotation: {annotation}")
print(f"Type: {type(annotation)}")
print(f"contains_aggregate: {getattr(annotation, 'contains_aggregate', 'Not found')}")
print(f"contains_over_clause: {getattr(annotation, 'contains_over_clause', 'Not found')}")

# Try to resolve Sum("cumul_DJR") and see what gets passed to the validation
aggregate_expr = Sum("cumul_DJR")
print(f"\nAggregate expression: {aggregate_expr}")

# Let's manually see what gets resolved
from django.db.models.expressions import Col, Ref

# Let's look at what Ref("cumul_DJR", annotation) looks like
ref_expr = Ref("cumul_DJR", annotation) 
print(f"\nRef expression: {ref_expr}")
print(f"Ref type: {type(ref_expr)}")
print(f"Ref contains_aggregate: {getattr(ref_expr, 'contains_aggregate', 'Not found')}")
print(f"Ref contains_over_clause: {getattr(ref_expr, 'contains_over_clause', 'Not found')}")

# Let's see what gets passed into the aggregate validation
resolved_expr = aggregate_expr.resolve_expression(queryset.query, allow_joins=True, reuse=None, summarize=True)
print(f"\nResolved aggregate: {resolved_expr}")
print(f"Resolved type: {type(resolved_expr)}")

# Get the source expressions that will be checked
source_exprs = resolved_expr.get_source_expressions()
print(f"\nSource expressions for validation: {source_exprs}")
for i, expr in enumerate(source_exprs):
    print(f"  [{i}] {expr}")
    print(f"      Type: {type(expr)}")
    print(f"      contains_aggregate: {getattr(expr, 'contains_aggregate', 'Not found')}")
    print(f"      contains_over_clause: {getattr(expr, 'contains_over_clause', 'Not found')}")
    if hasattr(expr, 'target'):
        print(f"      target: {expr.target}")
        print(f"      target.contains_aggregate: {getattr(expr.target, 'contains_aggregate', 'Not found')}")
        print(f"      target.contains_over_clause: {getattr(expr.target, 'contains_over_clause', 'Not found')}")