"""Add OneToOne user field to Juez and create User objects for existing Juez rows.

This migration adds a nullable OneToOneField `user` to `Juez` and populates it by
creating Django `User` accounts for any Juez without one.
"""
from django.db import migrations, models
from django.conf import settings


def create_users_for_jueces(apps, schema_editor):
    Juez = apps.get_model('app', 'Juez')
    # Use the auth User model (project uses default)
    try:
        User = apps.get_model('auth', 'User')
    except LookupError:
        return

    for juez in Juez.objects.filter(user__isnull=True):
        # derive a safe username from nombre
        raw = (juez.nombre or 'juez').strip().replace(' ', '_')[:150]
        username = raw or 'juez'
        base = username
        i = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}_{i}"
            i += 1
        # create a user with a random password
        try:
            user = User.objects.create_user(username=username, password=User.objects.make_random_password())
        except Exception:
            # fallback to simple create without hashing (unlikely)
            user = User.objects.create(username=username)
        juez.user = user
        juez.save(update_fields=['user'])


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_add_time_components'),
    ]

    operations = [
        migrations.AddField(
            model_name='juez',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='juez_profile', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(create_users_for_jueces, reverse_code=migrations.RunPython.noop),
    ]
