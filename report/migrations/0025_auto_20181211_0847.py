# Generated by Django 2.1.1 on 2018-12-11 08:47

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('report', '0024_subproject_team'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='Report_date',
            field=models.DateField(default=datetime.date(2018, 12, 11)),
            preserve_default=False,
        ),
    ]