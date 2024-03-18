# Generated by Django 4.1.8 on 2023-06-28 06:07

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("netdoc", "0008_alter_discoverable_device"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="routetableentry",
            unique_together={
                (
                    "device",
                    "destination",
                    "distance",
                    "metric",
                    "protocol",
                    "vrf",
                    "nexthop_if",
                    "nexthop_ip",
                )
            },
        ),
    ]
