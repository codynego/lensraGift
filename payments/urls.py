from django.urls import path
from .views import PaymentInitializeView, PaymentVerifyView, PaymentListView

app_name = 'payments'

urlpatterns = [
    path('initialize/', PaymentInitializeView.as_view(), name='payment-initialize'),
    path('verify/', PaymentVerifyView.as_view(), name='payment-verify'),
    path('', PaymentListView.as_view(), name='payment-list'),
]
