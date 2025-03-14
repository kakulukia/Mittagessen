# Generated by Django 4.2.17 on 2025-02-27 09:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("invoices", "0011_alter_invoiceday_options_alter_invoicemeal_options_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="invoice",
            name="days",
        ),
        migrations.AddField(
            model_name="invoiceday",
            name="invoice",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="days",
                to="invoices.invoice",
            ),
        ),
    ]
