import requests
from django.conf import settings
from django.shortcuts import render

def index(request):
    # city from query param, default to Thane
    city = request.GET.get('city', 'Thane')
    api_key = settings.OPENWEATHER_API_KEY

    weather = {}
    try:
        url = f'http://api.openweathermap.org/data/2.5/weather'
        params = {'q': city, 'appid': api_key, 'units': 'metric'}
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        data = r.json()

        weather = {
            'city': f"{data.get('name')}, {data.get('sys', {}).get('country')}",
            'temp': round(data['main']['temp']),
            'feels_like': round(data['main']['feels_like']),
            'desc': data['weather'][0]['description'].title(),
            'icon': data['weather'][0]['icon'],   # you can map to your icons
            'humidity': data['main']['humidity'],
            'wind': data['wind']['speed'],
        }
    except Exception as e:
        weather['error'] = "Could not fetch weather data."

    context = {
        'weather': weather,
        'city_query': city,
    }
    return render(request, 'index.html', context)
from django.shortcuts import render

# Create your views here.
