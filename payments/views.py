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

class PaymentInitializeView(APIView):
    """View to start a payment (supports Next.js localStorage session_id)."""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        print("\n--- PAYMENT INITIALIZE START ---")
        print(f"Request Data: {request.data}")

        # 1. Validate incoming data
        serializer = PaymentInitializeSerializer(data=request.data)
        if not serializer.is_valid():
            print(f"Serializer Errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order_id = serializer.validated_data['order_id']
        email = serializer.validated_data['email']
        provided_session_id = serializer.validated_data.get('session_id')

        print(f"Validated: OrderID={order_id}, Email={email}, Session={provided_session_id}")

        try:
            # 2. Secure Order Retrieval
            if request.user.is_authenticated:
                print(f"Auth User: {request.user}")
                order = Order.objects.get(id=order_id, user=request.user)
            else:
                print(f"Guest User - Checking session: {provided_session_id}")
                # Security: Ensure guest only pays for an order linked to their session
                order = Order.objects.get(id=order_id, session_id=provided_session_id)
            print(f"Order found: ID={order.id}, Total={order.total_amount}")
        except Order.DoesNotExist:
            print("ERROR: Order not found or session_id mismatch.")
            return Response({'error': 'Order not found or access denied.'}, status=status.HTTP_404_NOT_FOUND)

        # 3. Prevent Double Payment
        if order.is_paid:
            print(f"ERROR: Order {order.id} is already paid.")
            return Response({'error': 'This order has already been paid for.'}, status=status.HTTP_400_BAD_REQUEST)

        # 4. Paystack Integration
        paystack_url = 'https://api.paystack.co/transaction/initialize'
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        print(f"Initializing Paystack Transaction for Order {order.id}")
        print("Headers:", headers)
        print("secret key:", settings.PAYSTACK_SECRET_KEY)
        
        # Paystack amount must be in Kobo (Naira * 100)
        paystack_data = {
            'email': email,
            'amount': int(order.total_amount * 100),
            'currency': 'NGN',
            'metadata': {
                'order_id': order.id,
                'session_id': provided_session_id
            }
        }

        try:
            print("Sending to Paystack...")
            response = requests.post(paystack_url, json=paystack_data, headers=headers)
            res_json = response.json()
            print(f"Paystack Response Status: {response.status_code}")
            print(f"Paystack Response Body: {res_json}")

            if response.status_code == 200 and res_json.get('status'):
                pay_info = res_json['data']
                
                # 5. Create Payment Record
                payment = Payment.objects.create(
                    order=order,
                    user=request.user if request.user.is_authenticated else None,
                    session_id=None if request.user.is_authenticated else provided_session_id,
                    reference=pay_info['reference'],
                    amount=order.total_amount,
                    access_code=pay_info.get('access_code', ''),
                    authorization_url=pay_info.get('authorization_url', ''),
                    paystack_response=res_json
                )
                print(f"Payment Record Created: Ref={payment.reference}")
                return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
            
            print(f"Paystack Initialization Failed: {res_json.get('message')}")
            return Response({'error': 'Paystack: ' + res_json.get('message', 'Initialization failed')}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            print(f"EXCEPTION: {str(e)}")
            return Response({'error': 'Internal server error: ' + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentVerifyView(APIView):
    """View to check if the payment was successful."""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        print("\n--- PAYMENT VERIFICATION START ---")
        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reference = serializer.validated_data['reference']
        print(f"Verifying Reference: {reference}")

        try:
            payment = Payment.objects.get(reference=reference)
        except Payment.DoesNotExist:
            print("ERROR: Payment record not found in DB.")
            return Response({'error': 'Payment record not found'}, status=status.HTTP_404_NOT_FOUND)

        paystack_url = f'https://api.paystack.co/transaction/verify/{reference}'
        headers = {'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}
        print(f"Sending verification request to Paystack: {paystack_url}")
        print("Headers:", headers)
        print("secret key:", settings.PAYSTACK_SECRET_KEY)

        try:
            response = requests.get(paystack_url, headers=headers)
            res_data = response.json()
            print(f"Paystack Verify Response: {res_data}")

            if response.status_code == 200 and res_data.get('status'):
                if res_data['data']['status'] == 'success':
                    payment.status = 'success'
                    payment.save()

                    order = payment.order
                    order.is_paid = True
                    order.paid_at = timezone.now()
                    order.status = 'processing'
                    order.save()
                    
                    print(f"SUCCESS: Order {order.id} marked as PAID.")
                    return Response({'message': 'Paid successfully'})
                
                payment.status = 'failed'
                payment.save()
                print("PAYMENT FAILED on Paystack side.")
                return Response({'error': 'Payment failed'}, status=status.HTTP_400_BAD_REQUEST)
            
            print("VERIFICATION FAILED: Paystack did not return success status.")
            return Response({'error': 'Verification failed'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"VERIFY EXCEPTION: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentListView(generics.ListAPIView):
    """Lists payments (Only for logged-in users)."""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)