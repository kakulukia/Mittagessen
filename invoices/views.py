import datetime

from django.db.models import Q
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from invoices.models import Customer, InvoiceDay, InvoiceMeal, Invoice
from invoices.serializers import CustomerSerializer, InvoiceDaySerializer, InvoiceMealSerializer, InvoiceSerializer, \
    InvoiceDayWithCustomerSerializer


class CustomerViewSet(ModelViewSet):
    queryset = Customer.data.all()
    serializer_class = CustomerSerializer

    @action(detail=True, methods=['get'], url_path='invoice-days')
    def invoice_days(self, request, pk=None):
        customer = self.get_object()
        qs = customer.invoice_days.filter()  # TODO: nur die letzten 90 Tage oder so übertragen
        return Response(InvoiceDaySerializer(qs, many=True).data)

    @action(detail=True, methods=['post'], url_path='generate-invoice')
    def generate_invoice(self, request, pk=None):
        customer = self.get_object()

        invoice_text = request.data.get("invoiceText", None)
        if not invoice_text:
            return Response({"message": "Es muss ein Text für die Rechnung angegeben werden."}, status=400)

        # Check if there are undelivered days in the month to be invoiced
        invoice_days = customer.invoice_days.filter(invoice__isnull=True)
        if not invoice_days.exists():
            return Response({"message": "Es gibt keine offenen Tage für eine neue Rechnung."}, status=400)
        first = invoice_days.first().date
        undelivered = invoice_days.filter(date__month=first.month, date__year=first.year, delivered=False)
        if undelivered.exists():
            return Response({"message": "Es gibt noch offene Tage. Die Rechnung kann noch nicht erstellt werden."}, status=400)

        new_invoice = Invoice.create_from_open_days(customer, invoice_text)
        return Response({"invoice_id": new_invoice.id})

    @action(detail=True, methods=['get'], url_path='invoices')
    def invoices(self, request, pk=None):
        """
        Return all invoices associated with this customer.
        """
        customer = self.get_object()
        invoices = customer.invoices.all()
        return Response(InvoiceSerializer(invoices, many=True).data)


class InvoiceDayViewSet(ModelViewSet):
    queryset = InvoiceDay.objects.all()
    serializer_class = InvoiceDaySerializer

    @action(detail=True, methods=['get'], url_path='meals')
    def meals(self, request, pk=None):
        day = self.get_object()
        return Response(InvoiceMealSerializer(day.meals.all(), many=True).data)

    @action(detail=False, methods=['get'], url_path='today')
    def today(self, request):
        today = datetime.date.today()
        qs = InvoiceDay.objects.filter(date=today)
        return Response(InvoiceDayWithCustomerSerializer(qs, many=True).data)


class InvoiceMealViewSet(ModelViewSet):
    queryset = InvoiceMeal.objects.all()
    serializer_class = InvoiceMealSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['day']


class InvoiceViewSet(ModelViewSet):
    queryset = Invoice.data.all()
    serializer_class = InvoiceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['customer']

    @action(detail=True, methods=['get'], url_path='pdf')
    def pdf(self, request, pk=None):
        invoice = self.get_object()
        pdf_data = invoice.generate_pdf()
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="Rechnung.pdf"'
        return response

    @action(detail=True, methods=['get'], url_path='days')
    def days(self, request, pk=None):
        invoice = self.get_object()
        qs = InvoiceDay.data.filter(invoice=invoice)
        return Response(InvoiceDaySerializer(qs, many=True).data)

    def perform_update(self, serializer):
        instance = serializer.save()
        instance.update_prices()
        instance.save()
