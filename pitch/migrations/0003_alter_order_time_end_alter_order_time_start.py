# Generated by Django 4.2.3 on 2023-07-26 04:26

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pitch', '0002_alter_order_status_alter_order_time_end_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='time_end',
            field=models.DateTimeField(default=datetime.datetime(2023, 7, 26, 4, 26, 11, 455871, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='order',
            name='time_start',
            field=models.DateTimeField(default=datetime.datetime(2023, 7, 26, 4, 26, 11, 455871, tzinfo=datetime.timezone.utc)),
        ),
    ]