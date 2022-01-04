from django.urls import path

from . import views as stripe_views
from rest_framework import routers

router = routers.SimpleRouter(trailing_slash=False)
# router.register(r'payment/', stripe_views.StripePayment, basename='payment'),
# router.register(r'repayment-classes/', stripe_views.RepaymentClasses, basename='repayment_classes'),
urlpatterns = [
    path("create-payment-intent", stripe_views.createpayment),
    path('repayment-classes/', stripe_views.RepaymentClasses.as_view(), name="repayment_classes"),
    path('payment/', stripe_views.StripePayment.as_view(), name="make_payment"),
    path('payment-detail/<id>', stripe_views.PaymentDetail.as_view(), name="payment_detail")

]
urlpatterns += router.urls
