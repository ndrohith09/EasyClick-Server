# Generated by Django 4.2.1 on 2023-12-01 07:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0009_rename_group_squaresubmodel_company_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriptionmodel',
            name='analytics_key',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
