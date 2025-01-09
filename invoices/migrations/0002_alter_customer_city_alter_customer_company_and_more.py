# Generated by Django 4.2.16 on 2024-12-13 16:58

from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ("invoices", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customer",
            name="city",
            field=models.CharField(max_length=200, verbose_name="Stadt"),
        ),
        migrations.AlterField(
            model_name="customer",
            name="company",
            field=models.CharField(blank=True, max_length=200, verbose_name="Firma"),
        ),
        migrations.AlterField(
            model_name="customer",
            name="email",
            field=models.EmailField(blank=True, max_length=254, verbose_name="E-Mail"),
        ),
        migrations.AlterField(
            model_name="customer",
            name="salutation",
            field=models.CharField(
                choices=[("Herr", "Herr"), ("Frau", "Frau")], max_length=200, verbose_name="Anrede"
            ),
        ),
        migrations.AlterField(
            model_name="customer",
            name="street",
            field=models.CharField(max_length=200, verbose_name="Straße"),
        ),
        migrations.AlterField(
            model_name="customer",
            name="zip",
            field=models.CharField(max_length=5, verbose_name="PLZ"),
        ),
        migrations.CreateModel(
            name="Invoice",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="created"),
                ),
                ("modified", models.DateTimeField(auto_now=True)),
                ("deleted", models.DateTimeField(editable=False, null=True)),
                ("concealed", models.BooleanField(default=False, editable=False)),
                (
                    "invoice_number",
                    models.CharField(max_length=200, verbose_name="Rechnungsnummer"),
                ),
                ("date", models.DateField(verbose_name="Lieferdatum")),
                ("items", models.JSONField(verbose_name="Positionen")),
                (
                    "net",
                    models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Netto"),
                ),
                (
                    "tax",
                    models.DecimalField(decimal_places=2, max_digits=10, verbose_name="MwSt."),
                ),
                (
                    "total",
                    models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Brutto"),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invoices",
                        to="invoices.customer",
                    ),
                ),
            ],
            options={
                "verbose_name": "Rechnung",
                "verbose_name_plural": "Rechnungen",
                "ordering": ["-date"],
                "get_latest_by": "created",
                "abstract": False,
                "base_manager_name": "data",
                "default_manager_name": "data",
            },
            managers=[
                ("data", django.db.models.manager.Manager()),
            ],
        ),
    ]
