# Generated by Django 4.2 on 2023-04-19 01:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('AlchemyApp', '0002_controlfamily_family_abbreviation_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='nistcontrol',
            name='control_family_abbv',
        ),
    ]
