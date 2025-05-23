# Generated by Django 5.1.7 on 2025-03-29 21:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_property_is_available_rental_rentpayment'),
    ]

    operations = [
        migrations.CreateModel(
            name='MaintenanceRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('request_date', models.DateTimeField(auto_now_add=True)),
                ('is_resolved', models.BooleanField(default=False)),
                ('resolved_date', models.DateTimeField(blank=True, null=True)),
                ('rental', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maintenance_requests', to='user.rental')),
            ],
        ),
    ]
