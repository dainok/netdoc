# Generated by Django 4.1.8 on 2023-06-27 07:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netdoc', '0008_alter_discoverable_device'),
    ]

    operations = [
        migrations.AddField(
            model_name='credential',
            name='verify_cert',
            field=models.BooleanField(default=True),
        ),
    ]