import os
import csv
import json
from collections import defaultdict
from django.conf import settings
from django.shortcuts import render

def dashboard(request):
    csv_path = os.path.join(settings.BASE_DIR, 'data', 'ev_data.csv')
    sessions = []
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # convert numeric fields
            for key in [
                'Energy Consumed (kWh)',
                'Charging Duration (hours)',
                'Charging Rate (kW)',
                'Charging Cost (USD)'
            ]:
                row[key] = float(row.get(key) or 0)
            sessions.append(row)

    # Display-friendly subset
    display_sessions = []
    for s in sessions:
        display_sessions.append({
            'user_id': s['User ID'],
            'vehicle_model': s['Vehicle Model'],
            'location': s['Charging Station Location'],
            'energy': s['Energy Consumed (kWh)'],
            'duration': s['Charging Duration (hours)'],
            'cost': s['Charging Cost (USD)'],
            'charger': s['Charger Type'],
        })

    # Summary metrics
    station_set = {s['Charging Station ID'] for s in sessions}
    total_energy = sum(s['Energy Consumed (kWh)'] for s in sessions)
    total_duration = sum(s['Charging Duration (hours)'] for s in sessions)
    avg_energy_all = total_energy / len(sessions) if sessions else 0
    avg_duration_all = total_duration / len(sessions) if sessions else 0

    # Vehicle Model avg energy
    model_data = defaultdict(list)
    for s in sessions:
        model_data[s['Vehicle Model']].append(s['Energy Consumed (kWh)'])
    model_labels = list(model_data.keys())
    model_avg = [sum(v)/len(v) for v in model_data.values()]

    # Day of week avg duration
    days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    day_map = defaultdict(list)
    for s in sessions:
        day_map[s['Day of Week']].append(s['Charging Duration (hours)'])
    day_avg = [sum(day_map[d])/len(day_map[d]) if day_map[d] else 0 for d in days]

    # Charger type avg rate
    charger_map = defaultdict(list)
    for s in sessions:
        charger_map[s['Charger Type']].append(s['Charging Rate (kW)'])
    charger_labels = list(charger_map.keys())
    charger_avg = [sum(v)/len(v) for v in charger_map.values()]

    # SOC scatter arrays
    start_soc = [float(s['State of Charge (Start %)'] or 0) for s in sessions]
    end_soc   = [float(s['State of Charge (End %)'] or 0) for s in sessions]

    # City-level metrics
    city_energy_map = defaultdict(list)
    city_cost_map = defaultdict(list)
    for s in sessions:
        city = s['Charging Station Location']
        city_energy_map[city].append(s['Energy Consumed (kWh)'])
        city_cost_map[city].append(s['Charging Cost (USD)'])
    city_labels = list(city_energy_map.keys())
    city_avg_energy = [sum(v)/len(v) for v in city_energy_map.values()]
    city_avg_cost   = [sum(v)/len(v) for v in city_cost_map.values()]

    context = {
        'display_sessions': display_sessions,
        'station_count': len(station_set),
        'avg_energy_all': avg_energy_all,
        'avg_duration_all': avg_duration_all,
        'model_labels': json.dumps(model_labels),
        'model_data': json.dumps(model_avg),
        'days': json.dumps(days),
        'day_data': json.dumps(day_avg),
        'charger_labels': json.dumps(charger_labels),
        'charger_data': json.dumps(charger_avg),
        'start_soc': json.dumps(start_soc),
        'end_soc': json.dumps(end_soc),
        'city_labels': json.dumps(city_labels),
        'city_energy': json.dumps(city_avg_energy),
        'city_cost': json.dumps(city_avg_cost),
    }
    return render(request, 'evdash/dashboard.html', context)
