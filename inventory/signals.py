from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import BrandingSettings


@receiver(post_save, sender=BrandingSettings)
def keep_single_branding(sender, instance, **kwargs):
    sender.objects.exclude(pk=instance.pk).delete()
