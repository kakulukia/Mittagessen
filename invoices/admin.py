from django.contrib import admin

from invoices.models import Customer, Invoice


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "street", "zip", "city", "email"]
    ordering = ["name"]
    search_fields = ["name", "email", "company"]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "date", "customer", "total"]
    ordering = ["-date"]
    search_fields = ["invoice_number", "customer__name"]
    list_filter = ["date", "customer"]

    fieldsets = [
        (None, {"fields": ["invoice_number", "date", "customer", "net", "tax", "total"]}),
    ]

    readonly_fields = ["invoice_number", "net", "tax", "total"]
