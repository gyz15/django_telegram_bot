from django.urls import path
from .views import FindStocks

urlpatterns = [
    path('test/', FindStocks.as_view()),
]
