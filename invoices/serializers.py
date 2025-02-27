from rest_framework import serializers

from invoices.models import Customer, InvoiceDay, InvoiceMeal, Invoice


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "address",
            "email",
            "delivery_type",
        ]


class InvoiceDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceDay
        fields = [
            "id",
            "date",
            "customer",
            "combining_dates",
            "delivered",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["meals"] = InvoiceMealSerializer(instance.meals.all(), many=True).data
        return data


class InvoiceMealSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceMeal
        fields = [
            "id",
            "name",
            "price",
            "count",
            "delivered",
            "day",
            "comment",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["showComment"] = False
        return data


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "date",
            "customer",
            "net",
            "tax",
            "total",
        ]

