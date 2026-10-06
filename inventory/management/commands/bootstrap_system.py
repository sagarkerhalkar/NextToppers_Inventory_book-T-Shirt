from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from inventory.models import BrandingSettings, TshirtBrand, TshirtStock, User


class Command(BaseCommand):
    help = "Create initial brands, branding record and the first Super Admin."

    def add_arguments(self, parser):
        parser.add_argument("--employee-id", required=True)
        parser.add_argument("--full-name", required=True)
        parser.add_argument("--mobile", required=True)
        parser.add_argument("--password", required=True)
        parser.add_argument("--email", default="")

    def handle(self, *args, **options):
        UserModel = get_user_model()
        employee_id = options["employee_id"].upper().strip()
        password = options["password"]
        if len(password) < 4:
            raise CommandError("Password must contain at least 4 characters.")
        if UserModel.objects.filter(employee_id=employee_id).exists():
            raise CommandError(f"Employee ID {employee_id} already exists.")
        UserModel.objects.create_superuser(
            employee_id=employee_id,
            full_name=options["full_name"],
            mobile_number=options["mobile"],
            password=password,
            email=options["email"],
        )
        for name, allowance in [("Next Toppers", 5), ("Nirmaan", 5), ("CUET", 1), ("Mission Jeet", 0)]:
            brand, _ = TshirtBrand.objects.get_or_create(name=name, defaults={"free_quantity_rolling_12_months": allowance})
            for size, _label in User.TshirtSize.choices:
                TshirtStock.objects.get_or_create(brand=brand, size=size)
        BrandingSettings.load()
        self.stdout.write(self.style.SUCCESS("Initial system setup completed."))
