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
            "bank_account",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["short_address"] = ', '.join(instance.address.split("\n")[1:]).replace(', ,', ',')
        return data


class InvoiceDaySerializer(serializers.ModelSerializer):

    class Meta:
        model = InvoiceDay
        fields = [
            "id",
            "date",
            "customer",
            "combining_dates",
            "delivered",
            "invoice",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["meals"] = InvoiceMealSerializer(instance.meals.all(), many=True).data
        return data


class InvoiceDayWithCustomerSerializer(InvoiceDaySerializer):
    customer = CustomerSerializer(read_only=True)


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
            "text",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["customer_name"] = instance.customer.name
        return data

