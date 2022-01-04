import json

from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework import status
import stripe
from rest_framework.views import APIView

from Appointment.models import Booking, ClassInstructor
from SharkDeck.constants import user_constants
from user.models import User
from .serializers import StripePaymentSerializer, RepaymentBookingSeralizer
from rest_framework.viewsets import ModelViewSet
from Appointment import models as appointment_model
from django.utils.crypto import get_random_string
from user.decorators import authorize
import logging
import os

# Get an instance of a logger
logger = logging.getLogger(__name__)

# stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
AP = "sk_test_51I5m0yEHlEuRL3ozIMJxb6pczvkic82sB7SOMqLsINQgVz1r7haG4zTk3knnHdOafC9WlsgkPmhV2D0dzYTwLKi900QKa1waJN"
stripe.api_key = "sk_test_51I5m0yEHlEuRL3ozIMJxb6pczvkic82sB7SOMqLsINQgVz1r7haG4zTk3knnHdOafC9WlsgkPmhV2D0dzYTwLKi900QKa1waJN"
Publisher_key = "pk_test_51I5m0yEHlEuRL3ozRkUrNrrBC4kXUXkOW2k5YH4gt2ifPCH2L3YXqj4hfoAs5ozRcq53VxR4FE4jIARw1SRkbxxb00jm1tgwlh"
# STRIPE_SECRET_KEY= os.environ.get("STRIPE_SECRET_KEY")
# Publisher_key= os.environ.get("STRIPE_PUBLISHER_KEY")
# stripe.api_key = STRIPE_SECRET_KEY

@csrf_exempt
def createpayment(request):
    if "email" in request.session:
        data = json.loads(request.body)
        # Create a PaymentIntent with the order amount and currency
        # print(data["booking_id"])
        booking_id = data["items"][0]["booking"]
        amount = int(float(data["amount"]) * 100)
        currency = data['currency']
        # stripe.PaymentIntent.api_key
        intent = stripe.PaymentIntent.create(
            description='Swim Time Solutions ',
            shipping={
                'name': 'null',
                'address': {
                    'line1': 'Null',
                    'postal_code': '98140',
                    'city': 'San Francisco',
                    'state': 'CA',
                    'country': 'US',
                },
                # "email": booking_id,
            },
            amount=amount,
            currency=currency,
            payment_method_types=['card'],
            metadata={"booking_id": booking_id, "payment_type": data["items"][0]["payment_type"]}

        )
        print(intent.client_secret)
        try:
            return JsonResponse({
                                    'publishableKey': Publisher_key,
                                    'clientSecret': intent.client_secret})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=403)
    else:
        return JsonResponse({'error': "You Are Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)


class PaymentDetail(APIView):
    def get(self,request,id):
        if appointment_model.Transaction.objects.filter(id=id).exists():
            transection_data = appointment_model.Transaction.objects.get(id=id)
            status = transection_data.booking.payment_status
            booking = transection_data.booking
            res_data = {
                'instructor': booking.class_instructor.instructor.get_full_name(),
                'total_day': booking.class_instructor.total_days,
                'time_slot': booking.class_instructor.time_slot,
                'transaction_id': transection_data.transaction_id,
                'status': status,
                'payment_type': booking.payment_type,
                'total_amount': booking.class_instructor.price,
                'paid_amount': booking.get_total_paid,
                'due_amount': booking.get_total_due,
            }
            return render(request, "payment_detail.html", {"data": res_data})
        else:
            return redirect("dashboard_view")


class StripePayment(APIView):
    # serializer_class = StripePaymentSerializer()
    http_method_names = ['post',]


    def post(self, request, *args, **kwargs):
        if request.method == "POST":
            if "email" in request.session:
                data = json.loads(request.data["payload"])
                if data["status"] == "succeeded":
                    # get Booking ID From The Intent Id That We Have Created Previously
                    intent_id = data["id"]
                    previous_intent = stripe.PaymentIntent.retrieve(intent_id)
                    booking = Booking.objects.get(id=int(previous_intent["metadata"]["booking_id"]))
                    payment_type = previous_intent["metadata"]["payment_type"]
                    transaction_id = data["id"]
                    payment_status = appointment_model.COMPLETED
                    paid_amount = (data["amount"])/100
                    due_amount = 0
                    print("Payment Success")
                    # payment_type = appointment_model.CARD
                    transaction_obj = appointment_model.Transaction.objects.create(
                        booking=booking, transaction_id=transaction_id,
                        status=payment_status, payment_type=payment_type,
                        total_amount=booking.class_instructor.price,
                        paid_amount=paid_amount,
                        due_amount=due_amount
                    )
                    try:
                        total_paid_amount = 0
                        booking = appointment_model.Booking.objects.get(id=booking.id)
                        for transaction in appointment_model.Transaction.objects.filter(booking=booking,
                                                                                        payment_type=appointment_model.CARD):
                            total_paid_amount = total_paid_amount + transaction.paid_amount

                        if booking.class_instructor.price == total_paid_amount:
                            booking.booking_payment_status = appointment_model.BOOKING_COMPLETED
                        else:
                            booking.booking_payment_status = appointment_model.PARTIALLY_BOOKED
                        booking.save()

                    except Exception:
                        transaction_obj.delete()
                        return Response({'error': 'Invalid Booking.'})
                    return redirect("payment_detail",id=transaction_obj.id)
                else:
                    print("payment Failed")
            else:
                return JsonResponse({'error': "You Are Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return  redirect(request,"dashboard_view")
        # serializer = StripePaymentSerializer(data=request.data, context={'user': request.user})
        # serializer.is_valid(raise_exception=True)
        # if serializer.validated_data['payment_type'] == '2':
        #     booking = serializer.validated_data['booking']
        #     try:
        #         token = stripe.Token.create(
        #             card={
        #                 "number": serializer.validated_data['card_num'],
        #                 "exp_month": serializer.validated_data['exp_month'],
        #                 "exp_year": serializer.validated_data['exp_year'],
        #                 "cvc": serializer.validated_data['cvc']
        #             },
        #
        #         )
        #
        #         charge = stripe.Charge.create(
        #             source=token,
        #             description='sharkDeck services',
        #             shipping={
        #                 'name': booking.user.get_full_name(),
        #                 'address': {
        #                     'line1': booking.user.address,
        #                     'postal_code': 'null',
        #                     'city': 'null',
        #                     'state': 'null',
        #                     'country': 'US',
        #                 },
        #
        #             },
        #             amount=serializer.validated_data['paid_amount'],
        #             currency='usd',
        #         )
        #
        #         if charge['captured']:
        #             transaction_id = charge.balance_transaction
        #             if charge.paid:
        #                 payment_status = appointment_model.COMPLETED
        #             else:
        #                 payment_status = appointment_model.PENDING
        #             payment_type = appointment_model.CARD
        #             transaction_obj = appointment_model.Transaction.objects.create(
        #                 booking=booking, transaction_id=transaction_id,
        #                 status=payment_status, payment_type=payment_type,
        #                 total_amount=booking.class_instructor.price,
        #                 paid_amount=serializer.validated_data['paid_amount'],
        #                 due_amount=serializer.validated_data['due_amount']
        #             )
        #             try:
        #                 total_paid_amount = 0
        #                 booking = appointment_model.Booking.objects.get(id=booking.id)
        #                 for transaction in appointment_model.Transaction.objects.filter(booking=booking,
        #                                                                                 payment_type=appointment_model.CARD):
        #                     total_paid_amount = total_paid_amount + transaction.paid_amount
        #
        #                 if booking.class_instructor.price == total_paid_amount:
        #                     booking.booking_payment_status = appointment_model.BOOKING_COMPLETED
        #                 else:
        #                     booking.booking_payment_status = appointment_model.PARTIALLY_BOOKED
        #                 booking.save()
        #
        #             except Exception:
        #                 transaction_obj.delete()
        #                 return Response({'error': 'Invalid Booking.'})
        #
        #             res_data = {
        #                 'instructor': booking.class_instructor.instructor.get_full_name(),
        #                 'total_day': booking.class_instructor.total_days,
        #                 'time_slot': booking.class_instructor.time_slot,
        #                 'transaction_id': transaction_id,
        #                 'status': payment_status,
        #                 'payment_type': payment_type,
        #                 'total_amount': booking.class_instructor.price,
        #                 'paid_amount': serializer.validated_data['paid_amount'],
        #                 'due_amount': serializer.validated_data['due_amount']
        #
        #             }
        #             return Response(res_data, status=status.HTTP_200_OK)
        #
        #         return Response({'error': 'payment failed'}, status=status.HTTP_400_BAD_REQUEST)
        #     except Exception as e:
        #         logger.exception(e)
        #         try:
        #             error = {'Status': e.http_status,
        #                      'Code': e.code,
        #                      'Param': e.param,
        #                      'Message': e.user_message
        #                      }
        #
        #             return Response(error, status=e.http_status)
        #         except:
        #             return Response({"error": "Something Went wrong"}, status=500)
        # else:
        #     transaction_id = 'txn_' + get_random_string(30)
        #     payment_status = appointment_model.PENDING
        #     payment_type = appointment_model.CASH
        #     booking = serializer.validated_data['booking']
        #     appointment_model.Transaction.objects.create(
        #         booking=booking, transaction_id=transaction_id,
        #         status=payment_status, payment_type=payment_type,
        #         total_amount=booking.class_instructor.price,
        #         paid_amount=serializer.validated_data['paid_amount'],
        #         due_amount=serializer.validated_data['due_amount']
        #     )
        #     booking.booking_payment_status = appointment_model.PARTIALLY_BOOKED
        #     booking.save()
        #     res_data = {
        #         'instructor': booking.class_instructor.instructor.get_full_name(),
        #         'total_day': booking.class_instructor.total_days,
        #         'time_slot': booking.class_instructor.time_slot,
        #         'transaction_id': transaction_id,
        #         'status': payment_status,
        #         'payment_type': payment_type,
        #         'total_amount': booking.class_instructor.price,
        #         'paid_amount': serializer.validated_data['paid_amount'],
        #         'due_amount': serializer.validated_data['due_amount']
        #
        #     }
        #     return Response(res_data, status=status.HTTP_200_OK)

class CashPayment(ModelViewSet):
    serializer_class = StripePaymentSerializer()
    http_method_names = ['post']

    # @authorize([user_constants.Trainee])
    def create(self, request, *args, **kwargs):
        serializer = StripePaymentSerializer(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        if 'email' in request.session:
            if serializer.validated_data['payment_type'] == '2':
                messages.error(request,"This URL only support cash payment")
                return redirect("dashboard_view")
            else:
                transaction_id = 'txn_' + get_random_string(30)
                payment_status = appointment_model.PENDING
                payment_type = appointment_model.CASH
                booking = serializer.validated_data['booking']
                paid_amount = float(serializer.validated_data['paid_amount'])
                appointment_model.Transaction.objects.create(
                    booking=booking, transaction_id=transaction_id,
                    status=payment_status, payment_type=payment_type,
                    total_amount=booking.class_instructor.price,
                    paid_amount=paid_amount,
                    due_amount=serializer.validated_data['due_amount']
                )
                booking.booking_payment_status = appointment_model.PARTIALLY_BOOKED
                booking.save()
                messages.success(request, "Cash Payment of "+str(paid_amount)+" is Done ")
                return redirect("dashboard_view")
        else:
            return redirect("dashboard_view")

class RepaymentClasses(APIView):

    # @authorize([user_constants.Trainee])
    def get(self, request):

        try:
            if 'email' in request.session:
                email = request.session['email']
                obj = User.objects.get(email=email)
                bookings = appointment_model.Booking.objects.filter(
                    user=User.objects.get(email=request.session['email'])).order_by('-id')
                ser = RepaymentBookingSeralizer(bookings, many=True)
                return render(request, "payment.html", {"data": ser.data,"user_details": obj})
            else:
                return redirect("dashboard_view")
        except Exception as e:
            return render(request, "payment.html")
