# Generated by Django 4.2.1 on 2023-12-03 07:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0010_subscriptionmodel_analytics_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='squaresubmodel',
            name='databricks_updated',
            field=models.BooleanField(default=False),
        ),
    ]
