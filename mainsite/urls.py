"""mainsite URL Configuration"""
from django.urls import include, path

urlpatterns = [
    path('api/quote', include('quotes_api.urls')),
]
