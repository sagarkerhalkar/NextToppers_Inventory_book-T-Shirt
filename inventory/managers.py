from django.contrib.auth.base_user import BaseUserManager


class EmployeeManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, employee_id, full_name, mobile_number, password=None, **extra_fields):
        if not employee_id:
            raise ValueError("Employee ID is required")
        if not full_name:
            raise ValueError("Full name is required")
        if not mobile_number:
            raise ValueError("Mobile number is required")
        user = self.model(
            employee_id=employee_id.upper().strip(),
            full_name=full_name.strip(),
            mobile_number=mobile_number.strip(),
            **extra_fields,
        )
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, employee_id, full_name, mobile_number, password=None, **extra_fields):
        extra_fields.setdefault("role", "SUPER_ADMIN")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(employee_id, full_name, mobile_number, password, **extra_fields)
