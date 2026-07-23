from django.db import DatabaseError
from django.db.backends.signals import connection_created
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import BrandingSettings


@receiver(post_save, sender=BrandingSettings)
def keep_single_branding(sender, instance, **kwargs):
    sender.objects.exclude(pk=instance.pk).delete()


@receiver(connection_created)
def optimise_sqlite_connection(sender, connection, **kwargs):
    if connection.vendor != "sqlite":
        return
    try:
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.execute("PRAGMA temp_store=MEMORY;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.execute("PRAGMA busy_timeout=30000;")
    except DatabaseError:
        return
