from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import RewardProfile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_reward_profile(sender, instance, created, **kwargs):
    if created:
        RewardProfile.objects.create(user=instance)