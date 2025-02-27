import datetime

from django.db.models import Q
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from invoices.models import Customer, InvoiceDay, InvoiceMeal, Invoice
from invoices.serializers import CustomerSerializer, InvoiceDaySerializer, InvoiceMealSerializer, InvoiceSerializer


class CustomerViewSet(ModelViewSet):
    queryset = Customer.data.all()
    serializer_class = CustomerSerializer

    @action(detail=True, methods=['get'], url_path='invoice-days')
    def invoice_days(self, request, pk=None):
        customer = self.get_object()
        # filter for either delivered false or date in the future
        day_filter = Q(delivered=False) | Q(date__gte=datetime.date.today())
        return Response(InvoiceDaySerializer(customer.invoice_days.filter(day_filter), many=True).data)

    @action(detail=True, methods=['get'], url_path='generate-invoice')
    def generate_invoice(self, request, pk=None):
        customer = self.get_object()

        new_invoice = Invoice.create_from_open_days(customer)
        if new_invoice is None:
            return Response({"error": "No open invoice days available for invoicing."}, status=400)
        pdf_data = new_invoice.generate_pdf()

        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="Rechnung.pdf"'
        return response

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
