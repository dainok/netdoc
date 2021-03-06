# Generated by Django 4.1.6 on 2023-02-12 09:11

from django.db import migrations, models
import utilities.json


class Migration(migrations.Migration):
    dependencies = [
        ("netdoc", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="arptableentry",
            name="custom_field_data",
            field=models.JSONField(
                blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder
            ),
        ),
        migrations.AlterField(
            model_name="credential",
            name="custom_field_data",
            field=models.JSONField(
                blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder
            ),
        ),
        migrations.AlterField(
            model_name="discoverable",
            name="custom_field_data",
            field=models.JSONField(
                blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder
            ),
        ),
        migrations.AlterField(
            model_name="discoverylog",
            name="custom_field_data",
            field=models.JSONField(
                blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder
            ),
        ),
        migrations.AlterField(
            model_name="macaddresstableentry",
            name="custom_field_data",
            field=models.JSONField(
                blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder
            ),
        ),
        migrations.AlterField(
            model_name="routetableentry",
            name="custom_field_data",
            field=models.JSONField(
                blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder
            ),
        ),
    ]
