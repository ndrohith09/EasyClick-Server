from django.urls import path
from .views import OpenGroupShareUrl, OpenGroupSharePaymentUrl
urlpatterns=[
    path('public-share/<str:url>',OpenGroupShareUrl.as_view(),name="open-group-share-url"), 
    path('public-share/<str:url>/payment',OpenGroupSharePaymentUrl.as_view(),name="open-group-share-payment"), 
]