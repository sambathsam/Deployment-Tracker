# Generated by Django 2.1.1 on 2018-11-23 06:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('report', '0018_auto_20181122_0904'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='Reportstatus',
            field=models.CharField(blank=True, default='Waiting', max_length=50),
        ),
    ]