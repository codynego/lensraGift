import requests
from django.conf import settings
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from orders.models import Order
from .models import Payment
from .serializers import (
    PaymentSerializer,
    PaymentInitializeSerializer,
    PaymentVerifySerializer
)
from django.utils import timezone
from digitalgifts.models import DigitalGift





# -----------------------------
# Views
# -----------------------------
class PaymentInitializeView(APIView):
    """Initialize payment for an Order or DigitalGift."""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PaymentInitializeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        email = data['email']
        provided_session_id = data.get('session_id')

        # Retrieve target: Order or DigitalGift
        target = None
        if data.get('order_id'):
            order_id = data['order_id']
            try:
                if request.user.is_authenticated:
                    target = Order.objects.get(id=order_id, user=request.user)
                else:
                    target = Order.objects.get(id=order_id, session_id=provided_session_id)
            except Order.DoesNotExist:
                return Response({'error': 'Order not found or access denied.'}, status=status.HTTP_404_NOT_FOUND)

            if target.is_paid:
                return Response({'error': 'This order has already been paid for.'}, status=status.HTTP_400_BAD_REQUEST)

            amount = target.total_amount

        elif data.get('digital_gift_id'):
            gift_id = data['digital_gift_id']
            try:
                if request.user.is_authenticated:
                    target = DigitalGift.objects.get(id=gift_id, user=request.user)
                else:
                    target = DigitalGift.objects.get(id=gift_id, session_id=provided_session_id)
            except DigitalGift.DoesNotExist:
                return Response({'error': 'Digital gift not found or access denied.'}, status=status.HTTP_404_NOT_FOUND)

            if target.is_paid:
                return Response({'error': 'This digital gift has already been paid for.'}, status=status.HTTP_400_BAD_REQUEST)

            amount = target.price

        # Initialize Paystack payment
        paystack_url = 'https://api.paystack.co/transaction/initialize'
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }

        paystack_data = {
            'email': email,
            'amount': int(amount * 100),  # Paystack uses Kobo
            'currency': 'NGN',
            'metadata': {
                'order_id': target.id if isinstance(target, Order) else None,
                'digital_gift_id': target.id if isinstance(target, DigitalGift) else None,
                'session_id': provided_session_id
            }
        }

        try:
            response = requests.post(paystack_url, json=paystack_data, headers=headers)
            res_json = response.json()

            if response.status_code == 200 and res_json.get('status'):
                pay_info = res_json['data']

                payment = Payment.objects.create(
                    order=target if isinstance(target, Order) else None,
                    digital_gift=target if isinstance(target, DigitalGift) else None,
                    user=request.user if request.user.is_authenticated else None,
                    session_id=None if request.user.is_authenticated else provided_session_id,
                    reference=pay_info['reference'],
                    amount=amount,
                    access_code=pay_info.get('access_code', ''),
                    authorization_url=pay_info.get('authorization_url', ''),
                    paystack_response=res_json
                )

                return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

            return Response({'error': 'Paystack initialization failed: ' + res_json.get('message', 'Unknown error')},
                            status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'error': 'Internal server error: ' + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentVerifyView(APIView):
    """Verify payment and update Order or DigitalGift."""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reference = serializer.validated_data['reference']

        try:
            payment = Payment.objects.get(reference=reference)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment record not found.'}, status=status.HTTP_404_NOT_FOUND)

        paystack_url = f'https://api.paystack.co/transaction/verify/{reference}'
        headers = {'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}

        try:
            response = requests.get(paystack_url, headers=headers)
            res_data = response.json()

            if response.status_code == 200 and res_data.get('status'):
                if res_data['data']['status'] == 'success':
                    payment.status = 'success'
                    payment.save()

                    # Mark target as paid
                    if payment.order:
                        payment.order.is_paid = True
                        payment.order.paid_at = timezone.now()
                        payment.order.status = 'processing'
                        payment.order.save()
                    elif payment.digital_gift:
                        payment.digital_gift.is_paid = True
                        payment.digital_gift.paid_at = timezone.now()
                        payment.digital_gift.status = 'ready'
                        payment.digital_gift.save()

                    return Response({'message': 'Payment successful.'})

                payment.status = 'failed'
                payment.save()
                return Response({'error': 'Payment failed.'}, status=status.HTTP_400_BAD_REQUEST)

            return Response({'error': 'Verification failed.'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentListView(generics.ListAPIView):
    """List payments for logged-in users."""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)
