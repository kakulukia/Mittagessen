from django.shortcuts import render


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
