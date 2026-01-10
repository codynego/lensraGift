import requests
from django.conf import settings
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
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


class PaymentInitializeView(APIView):
    """View for initializing payment with Paystack."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PaymentInitializeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data['order_id']
        email = serializer.validated_data['email']

        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if order.is_paid:
            return Response(
                {'error': 'Order already paid'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if payment already exists
        existing_payment = Payment.objects.filter(order=order).first()
        if existing_payment and existing_payment.status == 'pending':
            return Response(PaymentSerializer(existing_payment).data)

        # Initialize payment with Paystack
        paystack_url = 'https://api.paystack.co/transaction/initialize'
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        data = {
            'email': email,
            'amount': int(order.total_amount * 100),  # Convert to kobo
            'currency': 'NGN',
            'metadata': {
                'order_id': order.id,
                'order_number': order.order_number,
            }
        }

        try:
            response = requests.post(paystack_url, json=data, headers=headers)
            response_data = response.json()

            if response.status_code == 200 and response_data.get('status'):
                payment_data = response_data['data']
                
                payment = Payment.objects.create(
                    order=order,
                    user=request.user,
                    reference=payment_data['reference'],
                    amount=order.total_amount,
                    access_code=payment_data.get('access_code', ''),
                    authorization_url=payment_data.get('authorization_url', ''),
                    paystack_response=response_data
                )

                return Response(
                    PaymentSerializer(payment).data,
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {'error': 'Failed to initialize payment', 'details': response_data},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': f'Payment initialization failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentVerifyView(APIView):
    """View for verifying payment with Paystack."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reference = serializer.validated_data['reference']

        try:
            payment = Payment.objects.get(reference=reference, user=request.user)
        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify payment with Paystack
        paystack_url = f'https://api.paystack.co/transaction/verify/{reference}'
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        }

        try:
            response = requests.get(paystack_url, headers=headers)
            response_data = response.json()

            if response.status_code == 200 and response_data.get('status'):
                payment_status = response_data['data']['status']
                
                if payment_status == 'success':
                    payment.status = 'success'
                    payment.paystack_response = response_data
                    payment.save()

                    # Update order
                    order = payment.order
                    order.is_paid = True
                    order.paid_at = timezone.now()
                    order.payment_reference = reference
                    order.status = 'processing'
                    order.save()

                    return Response({
                        'message': 'Payment verified successfully',
                        'payment': PaymentSerializer(payment).data
                    })
                else:
                    payment.status = 'failed'
                    payment.paystack_response = response_data
                    payment.save()
                    
                    return Response(
                        {'error': 'Payment verification failed', 'details': response_data},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {'error': 'Failed to verify payment', 'details': response_data},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': f'Payment verification failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentListView(generics.ListAPIView):
    """View for listing user payments."""

    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)
