from typing import ClassVar

from rest_framework import serializers

from invoices.models import Customer, Invoice, InvoiceDay, InvoiceMeal


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "address",
            "email",
            "whatsapp_phone",
            "delivery_type",
            "bank_account",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["short_address"] = ', '.join(instance.address.split("\n")[1:]).replace(', ,', ',')
        return data


class InvoiceDaySerializer(serializers.ModelSerializer):
    source_message = serializers.CharField(
        required=False, allow_blank=True, trim_whitespace=False
    )

    class Meta:
        model = InvoiceDay
        fields = [
            "id",
            "date",
            "customer",
            "combining_dates",
            "delivered",
            "reviewed",
            "source_message",
            "invoice",
        ]

    def validate(self, attrs):
        if attrs.get("reviewed"):
            if not self.instance or not self.instance.meals.exists():
                raise serializers.ValidationError(
                    {"reviewed": "Bitte zuerst mindestens ein Gericht erfassen."}
                )
            if any(
                meal.count < 1 or meal.price < 0 or not meal.name.strip()
                for meal in self.instance.meals.all()
            ):
                raise serializers.ValidationError(
                    {"reviewed": "Bitte Gericht, Anzahl und Preis vor der Prüfung korrigieren."}
                )
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["meals"] = InvoiceMealSerializer(instance.meals.all(), many=True).data
        return data

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if validated_data.get("reviewed") and instance.reviewed:
            instance.meals.filter(price_needs_review=True).update(price_needs_review=False)
        return instance


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
            "price_needs_review",
        ]
        extra_kwargs: ClassVar = {
            "count": {"min_value": 1},
            "price": {"min_value": 0},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["showComment"] = False
        return data


class InvoiceSerializer(serializers.ModelSerializer):
    delivery_months = serializers.SerializerMethodField()

    def get_delivery_months(self, instance):
        return sorted({day.date.strftime("%Y-%m") for day in instance.days.all()})

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
            "delivery_months",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["customer_name"] = instance.customer.name
        return data
