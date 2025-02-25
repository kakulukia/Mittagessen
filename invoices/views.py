import datetime

from django.db.models import Q
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from invoices.models import Customer, InvoiceDay, InvoiceMeal
from invoices.serializers import CustomerSerializer, InvoiceDaySerializer, InvoiceMealSerializer


# Create your views here.
def generate_invoice(request):
    # Beispieldaten
    items = [
        {'name': 'Mittagessen', 'quantity': 4, 'price': 8, 'total': 32},
        {'name': 'Suppen', 'quantity': 1, 'price': 5, 'total': 15},
        {'name': 'Mittagessen', 'quantity': 4, 'price': 8, 'total': 32},
        {'name': 'Suppen', 'quantity': 1, 'price': 5, 'total': 15},
        {'name': 'Suppen', 'quantity': 1, 'price': 5, 'total': 15},
        {'name': 'Suppen', 'quantity': 1, 'price': 5, 'total': 15},
        {'name': 'Mittagessen', 'quantity': 4, 'price': 8, 'total': 32},
        {'name': 'Suppen', 'quantity': 1, 'price': 5, 'total': 15},
        {'name': 'Mittagessen', 'quantity': 4, 'price': 8, 'total': 32},
        {'name': 'Suppen', 'quantity': 1, 'price': 5, 'total': 15},
        {'name': 'Mittagessen', 'quantity': 4, 'price': 8, 'total': 32},
        {'name': 'Suppen', 'quantity': 1, 'price': 5, 'total': 15},
        {'name': 'Suppen', 'quantity': 1, 'price': 5, 'total': 15},
        {'name': 'Mittagessen', 'quantity': 4, 'price': 8, 'total': 32},
        # {'name': 'Suppen', 'quantity': 1, 'price': 5, 'total': 15},
        # {'name': 'Mittagessen', 'quantity': 4, 'price': 8, 'total': 32},
        # {'name': 'Suppen', 'quantity': 1, 'price': 5, 'total': 15},
        # {'name': 'Mittagessen', 'quantity': 4, 'price': 8, 'total': 32},
        # {'name': 'Suppen', 'quantity': 1, 'price': 5, 'total': 15},
        # {'name': 'Mittagessen', 'quantity': 4, 'price': 8, 'total': 32},
        # {'name': 'Suppen', 'quantity': 1, 'price': 5, 'total': 15},
    ]
    net = sum(item['total'] for item in items)
    tax = round(net * 0.07, 2)
    total = net + tax
    context = {
        'invoice_number': '2024-1001',
        'date': datetime.date.today().strftime('%d.%m.%Y'),
        'items': items,
        'net': net,
        'tax': tax,
        'total': total,
        'recipient': {
            'name': 'Max Mustermann',
            'street': 'Musterstraße 12',
            'zip': '12345',
            'city': 'Musterstadt',
        },
    }

    # HTML in PDF konvertieren
    html_string = render_to_string('invoice.pug', context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    print(html_string)
    pdf_file = html.write_pdf()

    # PDF als Antwort zurückgeben
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="Rechnung.pdf"'

    return response
    # return render(request, 'invoice.pug', context)


class CustomerViewSet(ModelViewSet):
    queryset = Customer.data.all()
    serializer_class = CustomerSerializer

    @action(detail=True, methods=['get'], url_path='invoice-days')
    def invoice_days(self, request, pk=None):
        customer = self.get_object()
        # filter for either delivered false or date in the future
        day_filter = Q(delivered=False) | Q(date__gte=datetime.date.today())
        return Response(InvoiceDaySerializer(customer.invoice_days.filter(day_filter), many=True).data)


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
