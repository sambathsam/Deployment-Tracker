# Generated by Django 2.1.1 on 2018-11-22 09:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('report', '0017_report_team'),
    ]

    operations = [
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Teamname', models.CharField(max_length=100, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='project',
            name='Team_name',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='report.Team'),
            preserve_default=False,
        ),
    ]
