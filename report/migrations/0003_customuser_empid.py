# Generated by Django 2.1.1 on 2018-11-13 06:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('report', '0002_remove_customuser_empid'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='Empid',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]