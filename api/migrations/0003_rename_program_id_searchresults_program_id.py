# Generated by Django 5.0.2 on 2024-02-11 19:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_remove_program_program_id_program_program_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='searchresults',
            old_name='program_Id',
            new_name='program_id',
        ),
    ]
