from django.shortcuts import render
from django.http import JsonResponse
from .utils import get_top_hashtags

def index(request):
    """Render the main page with D3.js visualization."""
    return render(request, 'index.html')

def trending_hashtags(request):
    """API endpoint for trending hashtags."""
    trends = get_top_hashtags(time_range='1h')
    return JsonResponse(trends, safe=False)
