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
from app.email_notification import mail_notification
from user.models import User, Kids, Profile
from .models import StripeAccount
from .serializers import StripePaymentSerializer, RepaymentBookingSeralizer
from rest_framework.viewsets import ModelViewSet
from Appointment import models as appointment_model
from django.utils.crypto import get_random_string
from user.decorators import authorize
import logging
import os
from SharkDeck import settings
from SharkDeck.tasks import sent_mail_task

BASE_URL = settings.BASE_URL
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

        booking = appointment_model.Booking.objects.get(id=booking_id)
        ser = RepaymentBookingSeralizer(booking)
        pending_amount = ser.get_pending_amount(booking)
        due_amount = booking.class_instructor.price - booking.get_total_paid - pending_amount

        # price = booking.class_instructor.price
        # print("prince", price)
        # print("due amount ", due_amount)
        # print('amount', data["amount"])
        #
        # if due_amount == price:
        #     if not (data["amount"] > price / 2):
        #         return JsonResponse({'error': "payment fail ! minimum 50% amount require in first payment."},
        #                             status=status.HTTP_406_NOT_ACCEPTABLE)

        if int(data["amount"]) > due_amount:
            return JsonResponse({'error': "Amount should not grater then due amount "},
                                status=status.HTTP_422_UNPROCESSABLE_ENTITY)
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
    def get(self, request, id):
        if appointment_model.Transaction.objects.filter(id=id).exists():
            transection_data = appointment_model.Transaction.objects.get(id=id)
            status = transection_data.booking.payment_status
            booking = transection_data.booking
            ser = RepaymentBookingSeralizer(Booking)
            email = request.session['email']
            user_details = User.objects.get(email=email)
            kid_detail = Kids.objects.filter(parent_id=user_details.id)
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
                'pending_amount': ser.get_pending_amount(booking),
            }
            return render(request, "payment_detail.html", {"data": res_data, "user_details":user_details, "kid_detail":kid_detail})
        else:
            return redirect("dashboard_view")


class StripePayment(APIView):
    # serializer_class = StripePaymentSerializer()
    http_method_names = ['post', ]

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
                    paid_amount = (data["amount"]) / 100
                    booking1 = appointment_model.Booking.objects.get(id=booking.id)
                    ser = RepaymentBookingSeralizer(booking1)
                    pending_amount = ser.get_pending_amount(booking1)
                    due_amount = booking1.class_instructor.price - booking1.get_total_paid - pending_amount
                    if paid_amount > due_amount:
                        messages.error("You have paid more then due amount contact support team form refund ")
                        return redirect("dashboard_view")
                    due_amount = 0
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
                        user_name = booking.user.get_full_name()

                        if booking.class_instructor.price == total_paid_amount:
                            booking.booking_payment_status = appointment_model.BOOKING_COMPLETED
                        else:
                            booking.booking_payment_status = appointment_model.PARTIALLY_BOOKED
                        booking.save()
                        user_email = booking.user.email
                        paid_amount = int((data["amount"]) / 100)
                        if paid_amount >= booking.class_instructor.price / 2:
                            inst_name = ClassInstructor.objects.get(id=booking.class_instructor.id)
                            instructor_name = inst_name.instructor.get_full_name()
                            email_body = f"Dear {user_name}," \
                                         f"\n\nHope you are doing well. This mail is to inform you that your Swimming classes have been scheduled.\n" \
                                         f"Please find below the details: \nClass - {booking.class_instructor.title} \n" \
                                         f"Instructore - {instructor_name}\nTotal days - {booking.class_instructor.total_days} days\n" \
                                         f"Time Slot - {booking.class_instructor.time_slot} minutes(Per Session)\n" \
                                         f"Fees - {booking.class_instructor.price} USD\n" \
                                         f"Paid Amount - {paid_amount} USD\n\n" \
                                         f"Thank You,\nTeam Swim Time Solutions"
                            # f"Due Amount - {due_amount} USD\n\n" \

                            subject = f"Booking Confirmation - Swim Time Solutions"
                            try:
                                # sent_mail_task.apply_async(kwargs={'subject': subject, 'email_body': email_body,
                                #                                    'user_email': user_email})
                                mail_notification(request, subject, email_body, user_email)
                            except Exception as e:
                                pass

                            instructor_name = inst_name.instructor.get_full_name()
                            email_body = f"Dear {instructor_name}," \
                                         f"\n\nHope you are doing well. This mail is to inform you that Swimming classes have been booked for you.\n" \
                                         f"Here is the Detail: \nClass - {booking.class_instructor.title} \n" \
                                         f"Student Name - {booking.kids.kids_name}\nParent Name - {user_name}\nTotal days - {booking.class_instructor.total_days} days\n" \
                                         f"Time Slot - {booking.class_instructor.time_slot} minutes(Per Session)\n" \
                                         f"Fees - {booking.class_instructor.price} USD\n" \
                                         f"Paid Amount - {paid_amount} USD\n\n" \
                                         f"Thank You,\nTeam Swim Time Solutions"
                            instructor_email = inst_name.instructor.email
                            try:
                                # sent_mail_task.apply_async(kwargs={'subject': subject, 'email_body': email_body,
                                #                                    'user_email': instructor_email})
                                mail_notification(request, subject, email_body, instructor_email)
                            except Exception as e:
                                pass
                        else:
                            subject = f"Repayment - Swim Time Solutions"
                            email_body = f"Hello {user_name}," \
                                         f"\n\nThis mail is to inform you that you have made payment of {paid_amount} USD.\n\n" \
                                         f"Thank You,\nTeam Swim Time Solutions"
                            try:
                                # sent_mail_task.apply_async(kwargs={'subject': subject, 'email_body': email_body,
                                #                                    'user_email': user_email})
                                mail_notification(request, subject, email_body, user_email)
                            except Exception as e:
                                pass

                    except Exception:
                        transaction_obj.delete()
                        return Response({'error': 'Invalid Booking.'})
                    return redirect("payment_detail", id=transaction_obj.id)
                else:
                    print("payment Failed")
            else:
                return JsonResponse({'error': "You Are Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return redirect(request, "dashboard_view")


class CashPayment(ModelViewSet):
    serializer_class = StripePaymentSerializer()
    http_method_names = ['post']

    # @authorize([user_constants.Trainee])
    def create(self, request, *args, **kwargs):
        serializer = StripePaymentSerializer(data=request.data, context={'user': request.user})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            # for i in list(e.args):
                # messages.error(request, i)
            return redirect("repayment_classes")
        if 'email' in request.session:
            if serializer.validated_data['payment_type'] == '2':
                messages.error(request, "This URL only support cash payment")
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
                messages.success(request, "Cash Payment of " + str(paid_amount) + " is Done ")

                user_name = booking.user.get_full_name()
                user_email = booking.user.email
                paid_amount_int = serializer.validated_data['paid_amount']
                if paid_amount >= booking.class_instructor.price / 2:
                    due_amount = serializer.validated_data['due_amount']
                    inst_name = ClassInstructor.objects.get(id=booking.class_instructor.id)
                    instructor_email = inst_name.instructor.email
                    # email = [user_email, instructor_mail]
                    instructor_name = inst_name.instructor.get_full_name()
                    subject = f"Booking Confirmation - Swim Time Solutions"
                    email_body = f"Dear {user_name}," \
                                 f"\n\nHope you are doing well. This mail is to inform you that your Swimming classes have been scheduled.\n" \
                                 f"Please find below the details: \nClass - {booking.class_instructor.title} \n" \
                                 f"Instructor - {instructor_name}\nTotal days - {booking.class_instructor.total_days} days\n" \
                                 f"Time Slot - {booking.class_instructor.time_slot} minutes(Per Session)\n" \
                                 f"Fees - {booking.class_instructor.price} USD\n" \
                                 f"Paid Amount - {paid_amount_int} USD\n" \
                                 f"Due Amount - {due_amount} USD\n\n" \
                                 f"Thank You,\nTeam Swim Time Solutions"
                    try:

                        # sent_mail_task.apply_async(kwargs={'subject': subject, 'email_body': email_body,
                        #                                    'user_email': user_email})
                        mail_notification(request, subject, email_body, user_email)
                    except Exception as e:
                        pass
                    email_body = f"Dear {instructor_name}," \
                                 f"\n\nHope you are doing well. This mail is to inform you that Swimming classes have been booked for you.\n" \
                                 f"Please find below the details: \nClass - {booking.class_instructor.title} \n" \
                                 f"Student Name - {booking.kids.kids_name}\nParent Name - {user_name}\nTotal days - {booking.class_instructor.total_days} days\n" \
                                 f"Time Slot - {booking.class_instructor.time_slot} minutes(Per Session)\n" \
                                 f"Fees - {booking.class_instructor.price} USD\n" \
                                 f"Paid Amount - {paid_amount_int} USD\n" \
                                 f"Due Amount - {due_amount} USD\n\n" \
                                 f"Thank You,\nTeam Swim Time Solutions"
                    try:
                        # sent_mail_task.apply_async(kwargs={'subject': subject, 'email_body': email_body,
                        #                                    'user_email': instructor_email})
                        mail_notification(request, subject, email_body, instructor_email)
                    except Exception as e:
                        pass
                else:
                    subject = f"Repayment Mail"
                    email_body = f"Hello {user_name}," \
                                 f"\n\nThis mail is to inform you that you have made payment of {paid_amount} USD. Your Due amount is {serializer.validated_data['due_amount']} USD\n\n" \
                                 f"Thank You,\nTeam Swim Time Solutions"
                    try:
                        # sent_mail_task.apply_async(kwargs={'subject': subject, 'email_body': email_body,
                        #                                    'user_email': user_email})
                        mail_notification(request, subject, email_body, user_email)
                    except Exception as e:
                        pass
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

                obj = User.objects.get(email=request.session['email'])
                user_id = obj.inst_id
                profile_detail = Profile.objects.filter(user_id=user_id)

                kid_detail = Kids.objects.filter(parent_id=obj.id)
                return render(request, "payment.html",
                              {"data": ser.data, "profile_detail": profile_detail, "user_details": obj, 'kid_detail': kid_detail, "BASE_URL": BASE_URL})

            else:
                return redirect("dashboard_view")
        except Exception as e:
            return render(request, "payment.html")


# For Connecting strip api a

# To Create a URL
class ConnectStripUrl(APIView):
    def get(self, request):
        '''
        Creating a account id , Note that we are using standard ,,
            we have Two options Standard and express
        '''
        if StripeAccount.objects.filter(Instructor__email=request.session["instructor_email"]).exists():
            return redirect('InstructorDashboard:dashboard_view')
            # return JsonResponse({"error": "An Stripe Account Is Already Linked To This Instructor"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        # Create URL With this account id
        account_data = stripe.Account.create(type="standard")
        account_id = account_data["id"]
        create_strip_url = stripe.AccountLink.create(

            account=account_id,
            refresh_url=BASE_URL + "/stripe/handle-redirect/",
            return_url=BASE_URL + "/stripe/handle-redirect/",
            type="account_onboarding",
        )

        if "account_id" in request.session:
            try:
                stripe.Account.delete(request.session["account_id"])
            except:
                pass
        request.session["account_id"] = account_id
        url_to_create_account = create_strip_url["url"]
        return redirect(url_to_create_account)
        # return JsonResponse({"url":url_to_create_account},status=status.HTTP_200_OK)


# To Handle A URL
class HandleRedirect(APIView):
    def get(self, request):
        # Checking if completed
        if "account_id" in request.session:
            account_id = request.session["account_id"]
            account = stripe.Account.retrieve(account_id)
            if account["business_profile"]["mcc"]:
                instructor = request.session["instructor_email"]
                save_stripe = StripeAccount(Instructor=User.objects.get(email=instructor), Account_ID=account_id)
                save_stripe.save()
                messages.success(request, "Account Created Successfully")
            else:
                # perform Delete action
                try:
                    if account_id:
                        stripe.Account.delete(account_id)
                    else:
                        pass
                except:
                    pass
                messages.error(request, "Can't Create Account")
        else:
            messages.error(request, "Please Stay In The Same Window . Failed To Create Account ")
        return redirect('InstructorDashboard:dashboard_view')
