# Generated by Django 4.2.17 on 2025-01-26 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("invoices", "0007_invoiceday_customer_delivery_invoicemeal_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="customer",
            name="delivery",
        ),
        migrations.AddField(
            model_name="customer",
            name="delivery_type",
            field=models.CharField(
                blank=True,
                choices=[("takeaway", "Abholung"), ("delivery", "Lieferung")],
                max_length=200,
                verbose_name="Lieferart",
            ),
        ),
    ]
