# Generated by Django 4.1.8 on 2023-08-14 14:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('virtualization', '0034_standardize_description_comments'),
        ('dcim', '0167_module_status'),
        ('ipam', '0064_clear_search_cache'),
        ('netdoc', '0011_alter_credential_enable_password_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='arptableentry',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='routetableentry',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='arptableentry',
            name='virtual_interface',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='virtualization.vminterface'),
        ),
        migrations.AddField(
            model_name='discoverable',
            name='vm',
            field=models.OneToOneField(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='virtualization.virtualmachine'),
        ),
        migrations.AddField(
            model_name='routetableentry',
            name='nexthop_virtual_if',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='virtualization.vminterface'),
        ),
        migrations.AddField(
            model_name='routetableentry',
            name='vm',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='virtualization.virtualmachine'),
        ),
        migrations.AlterField(
            model_name='arptableentry',
            name='interface',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='dcim.interface'),
        ),
        migrations.AlterField(
            model_name='routetableentry',
            name='device',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='dcim.device'),
        ),
        migrations.AlterUniqueTogether(
            name='arptableentry',
            unique_together={('interface', 'ip_address', 'mac_address', 'virtual_interface')},
        ),
        migrations.AlterUniqueTogether(
            name='routetableentry',
            unique_together={('device', 'destination', 'distance', 'metric', 'protocol', 'vrf', 'nexthop_if', 'nexthop_virtual_if', 'nexthop_ip', 'vm')},
        ),
    ]
