from django.shortcuts import render
from django.conf import settings
from googlemaps import Client
import csv
import io

def optimizer_view(request):
    # Inicializa el cliente de Google Maps con la clave de settings.py
    gmaps = Client(key=settings.GOOGLE_MAPS_API_KEY)
    context = {}

    if request.method == 'POST':
        try:
            # --- 1. OBTENER EL PUNTO DE PARTIDA ---
            # Si se usó geolocalización, los datos vienen en lat/lon
            lat = request.POST.get('latitude')
            lon = request.POST.get('longitude')

            if lat and lon:
                start_location = f"{lat},{lon}"
            else:
                start_location = request.POST.get('start_point', '').strip()

            # --- 2. OBTENER LOS DESTINOS (DE CSV O TEXTO) ---
            destinations = []
            if 'csv_file' in request.FILES:
                csv_file = request.FILES['csv_file']
                # Decodificar el archivo en memoria
                decoded_file = csv_file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                # Leer cada fila (asumiendo que la dirección está en la primera columna)
                for row in csv.reader(io_string):
                    if row and row[0].strip():
                        destinations.append(row[0].strip())
            else:
                addresses_text = request.POST.get('addresses', '').strip()
                if addresses_text:
                    destinations = [addr.strip() for addr in addresses_text.split(';') if addr.strip()]

            # --- 3. VALIDAR ENTRADAS ---
            if not start_location or not destinations:
                context['error'] = "Please provide a starting point and at least one destination."
                return render(request, 'route_planner/optimizer.html', context)

            # --- 4. LLAMAR A LA API DE GOOGLE MAPS ---
            matrix = gmaps.distance_matrix(start_location, destinations, mode="driving")

            # --- 5. PROCESAR Y ORDENAR RESULTADOS ---
            results = []
            for i, element in enumerate(matrix['rows'][0]['elements']):
                if element['status'] == 'OK':
                    results.append({
                        'address': destinations[i],
                        'distance_text': element['distance']['text'],
                        'distance_value': element['distance']['value'],
                        'duration_text': element['duration']['text']
                    })
                else:
                    results.append({'address': f"{destinations[i]} (Not found)", 'distance_value': float('inf')})

            sorted_destinations = sorted(results, key=lambda x: x['distance_value'])

            # --- 6. GENERAR URL DE GOOGLE MAPS ---
            valid_addresses = [d['address'] for d in sorted_destinations if d['distance_value'] != float('inf')]
            if valid_addresses:
                origin_param = start_location
                destination_param = valid_addresses[-1]
                waypoints_param = "|".join(valid_addresses[:-1])
                maps_url = f"https://www.google.com/maps/dir/?api=1&origin={origin_param}&destination={destination_param}&waypoints={waypoints_param}"
                context['maps_url'] = maps_url

            context['sorted_destinations'] = sorted_destinations

        except Exception as e:
            context['error'] = f"An unexpected error occurred: {e}"

    return render(request, 'route_planner/optimizer.html', context)
