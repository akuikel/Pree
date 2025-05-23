# Generated by Django 5.2 on 2025-05-10 17:36

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0010_propertyimage'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='avatars/')),
                ('email_payment_reminders', models.BooleanField(default=True)),
                ('email_rental_expiry', models.BooleanField(default=True)),
                ('email_maintenance_updates', models.BooleanField(default=True)),
                ('email_promotions', models.BooleanField(default=False)),
                ('system_payment_reminders', models.BooleanField(default=True)),
                ('system_rental_expiry', models.BooleanField(default=True)),
                ('system_maintenance_updates', models.BooleanField(default=True)),
                ('system_promotions', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
