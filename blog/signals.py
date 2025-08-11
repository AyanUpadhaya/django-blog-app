# signals.py
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile, Post
import cloudinary.uploader #type: ignore
from urllib.parse import urlparse

User = get_user_model()

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


def get_public_id(file_field):
    """
    Extract public_id from a CloudinaryField or ImageField URL.
    """
    if hasattr(file_field, 'public_id'):
        return file_field.public_id
    elif file_field and hasattr(file_field, 'url'):
        path = urlparse(file_field.url).path
        return path.split("/")[-1].split(".")[0]
    return None


@receiver(pre_delete, sender=Post)
def delete_post_image_from_cloudinary(sender, instance, **kwargs):
    """
    Delete image from Cloudinary when post is deleted.
    """
    public_id = get_public_id(instance.featured_image)
    if public_id:
        cloudinary.uploader.destroy(public_id)


@receiver(pre_save, sender=Post)
def delete_old_image_on_update(sender, instance, **kwargs):
    """
    Delete old image from Cloudinary if image is cleared or replaced.
    """
    if not instance.pk:  # New object, skip
        return

    try:
        old_instance = Post.objects.get(pk=instance.pk)
    except Post.DoesNotExist:
        return

    if old_instance.featured_image and old_instance.featured_image != instance.featured_image:
        public_id = get_public_id(old_instance.featured_image)
        if public_id:
            cloudinary.uploader.destroy(public_id)