# myapp/urls.py
from django.urls import path
from .views import TaxOveragesView, DelawareCountyCourtScraper

urlpatterns = [
    path('', TaxOveragesView.as_view(), name='tax_overages'),
    path('scrap-county/', DelawareCountyCourtScraper.as_view(), name='scrap_county'),
]
