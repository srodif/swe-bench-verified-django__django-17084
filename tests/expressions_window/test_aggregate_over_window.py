"""
Test for aggregates over window functions.
"""

from django.test import TestCase, skipUnlessDBFeature

from .models import Employee
from django.db.models import Sum, F, Window, Avg
from django.db.models.functions import Coalesce


@skipUnlessDBFeature("supports_over_clause")
class AggregateOverWindowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Employee.objects.bulk_create([
            Employee(name="Alice", salary=50000, department="Engineering", hire_date="2020-01-15", age=25),
            Employee(name="Bob", salary=60000, department="Engineering", hire_date="2020-03-10", age=30),
            Employee(name="Carol", salary=55000, department="Sales", hire_date="2020-02-20", age=28),
            Employee(name="Dave", salary=65000, department="Sales", hire_date="2020-04-05", age=35),
        ])

    def test_sum_over_window_function(self):
        """
        Test that Sum can be applied over a window function annotation.
        This reproduces the issue from Django 4.2 where this would fail.
        """
        from django.db.models import FloatField
        queryset = Employee.objects.annotate(
            cumul_salary=Window(Sum("salary", output_field=FloatField()), order_by=F("hire_date").asc())
        )
        
        # This should work without raising FieldError or database errors
        result = queryset.aggregate(
            total_salary=Sum("salary"),
            cumul_salary_total=Sum("cumul_salary")
        )
        
        self.assertEqual(result['total_salary'], 230000)  # 50000 + 60000 + 55000 + 65000
        # cumul_salary_total should be the sum of running totals:
        # Alice: 50000, Carol: 105000, Bob: 165000, Dave: 230000
        # Total: 50000 + 105000 + 165000 + 230000 = 550000
        self.assertEqual(result['cumul_salary_total'], 550000)

    def test_multiple_aggregates_over_window_functions(self):
        """
        Test multiple different aggregates over window functions.
        """
        queryset = Employee.objects.annotate(
            cumul_salary=Window(Sum("salary"), order_by=F("hire_date").asc()),
            avg_salary_by_dept=Window(Avg("salary"), partition_by=["department"])
        )
        
        result = queryset.aggregate(
            cumul_sum=Sum("cumul_salary"),
            avg_of_avgs=Avg("avg_salary_by_dept")
        )
        
        self.assertEqual(result['cumul_sum'], 550000)
        # avg_salary_by_dept for Engineering: (50000 + 60000) / 2 = 55000
        # avg_salary_by_dept for Sales: (55000 + 65000) / 2 = 60000
        # avg_of_avgs: (55000 + 55000 + 60000 + 60000) / 4 = 57500
        self.assertEqual(result['avg_of_avgs'], 57500)