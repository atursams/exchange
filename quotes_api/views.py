from django.http import HttpResponse
from .rates import get_quote

import redis

async def index(request):
    try:
        result = await get_quote(**{key:value for key, value in request.GET.items()})
        return HttpResponse(result)
    except Exception as e:
        return HttpResponse(f"Error: {e}.")