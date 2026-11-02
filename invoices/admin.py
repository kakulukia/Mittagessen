from django.contrib import admin, messages

from invoices.models import Customer, Invoice, WhatsAppMessage


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "sender_phone", "customer", "received_at", "processed_at", "message_preview")
    search_fields = ("sender", "sender_phone", "customer__name", "text")
    list_filter = ("received_at",)
    readonly_fields = ("processed_at", "processing_error", "created", "modified")
    autocomplete_fields = ("customer",)

    @admin.display(description="Nachricht")
    def message_preview(self, obj):
        return obj.text[:120]

    def save_model(self, request, obj, form, change):
        already_processed = bool(obj.processed_at)
        super().save_model(request, obj, form, change)
        if obj.processing_error:
            self.message_user(request, obj.processing_error, level=messages.WARNING)
        elif already_processed:
            self.message_user(request, "Bereits angelegte Bestellungen bleiben unverändert. Korrekturen bitte in der Tagesübersicht vornehmen.")
        else:
            self.message_user(request, "Bestellungen wurden ungeprüft angelegt. Bitte in der Tagesübersicht prüfen.")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "whatsapp_phone"]
    ordering = ["name"]
    search_fields = ["name", "email", "address", "whatsapp_phone"]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "date", "customer", "total"]
    ordering = ["-date"]
    search_fields = ["invoice_number", "customer__name"]
    list_filter = ["date", "customer"]

    fieldsets = [
        (None, {"fields": ["invoice_number", "date", "customer", "net", "tax", "total", "text"]}),
    ]

    readonly_fields = ["invoice_number", "net", "tax", "total"]
