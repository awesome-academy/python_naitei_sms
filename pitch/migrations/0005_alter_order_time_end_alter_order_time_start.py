# Generated by Django 4.2.3 on 2023-08-08 11:08

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pitch', '0004_alter_order_time_end_alter_order_time_start'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='time_end',
            field=models.DateTimeField(default=datetime.datetime(2023, 8, 8, 11, 8, 50, 154281, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='order',
            name='time_start',
            field=models.DateTimeField(default=datetime.datetime(2023, 8, 8, 11, 8, 50, 154281, tzinfo=datetime.timezone.utc)),
        ),
    ]