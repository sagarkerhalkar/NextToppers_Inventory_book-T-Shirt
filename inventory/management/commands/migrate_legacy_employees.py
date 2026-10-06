from django.core.management.base import BaseCommand
from django.db import transaction

from inventory.models import BookAllocation, Employee, TshirtAllocation, User


class Command(BaseCommand):
    help = "Convert legacy allocation recipients stored as login users into non-login Employee records."

    @transaction.atomic
    def handle(self, *args, **options):
        created_count = 0
        linked_books = 0
        linked_tshirts = 0
        user_ids = set(BookAllocation.objects.filter(employee_record__isnull=True, employee__isnull=False).values_list("employee_id", flat=True))
        user_ids.update(TshirtAllocation.objects.filter(employee_record__isnull=True, employee__isnull=False).values_list("employee_id", flat=True))
        for user in User.objects.filter(pk__in=user_ids):
            employee, created = Employee.objects.get_or_create(
                employee_id=user.employee_id,
                defaults={
                    "full_name": user.full_name,
                    "mobile_number": user.mobile_number,
                    "email": user.email,
                    "department": user.department,
                    "designation": user.designation,
                    "joining_date": user.joining_date,
                    "office_location": user.office_location,
                    "default_tshirt_size": user.default_tshirt_size,
                    "is_active": user.is_active,
                    "notes": "Automatically created from legacy allocation data.",
                },
            )
            if created:
                created_count += 1
            linked_books += BookAllocation.objects.filter(employee=user, employee_record__isnull=True).update(employee_record=employee)
            linked_tshirts += TshirtAllocation.objects.filter(employee=user, employee_record__isnull=True).update(employee_record=employee)
        self.stdout.write(self.style.SUCCESS(f"Legacy migration completed: {created_count} employee record(s), {linked_books} Book allocation(s), {linked_tshirts} T-shirt allocation(s)."))
