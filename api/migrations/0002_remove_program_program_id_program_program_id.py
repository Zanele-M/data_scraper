# Generated by Django 5.0.2 on 2024-02-11 19:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='program',
            name='program_Id',
        ),
        migrations.AddField(
            model_name='program',
            name='program_id',
            field=models.IntegerField(default=4664828),
            preserve_default=False,
        ),
    ]
