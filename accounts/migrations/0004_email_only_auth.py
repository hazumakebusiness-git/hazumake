# Generated migration for email-based authentication

from django.db import migrations, models


def set_default_emails(apps, schema_editor):
    """Set default emails for any users without an email."""
    CustomUser = apps.get_model('accounts', 'CustomUser')
    users_without_email = CustomUser.objects.filter(email__isnull=True) | CustomUser.objects.filter(email='')
    for idx, user in enumerate(users_without_email):
        user.email = f"{user.username}+{idx}@no-reply.hazumake.local"
        user.save()


def reverse_default_emails(apps, schema_editor):
    """Reverse function - no-op for safety."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_remove_customuser_mlbb_user_id_and_more'),
    ]

    operations = [
        # First, set default emails for any users without email
        migrations.RunPython(set_default_emails, reverse_default_emails),
        
        # Then make email required and ensure it's unique
        migrations.AlterField(
            model_name='customuser',
            name='email',
            field=models.EmailField(blank=False, max_length=254, null=False, unique=True),
        ),
    ]
