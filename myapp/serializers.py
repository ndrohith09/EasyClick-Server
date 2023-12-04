from rest_framework.serializers import ModelSerializer
from .models import *

class UserSerializer(ModelSerializer):
    class Meta:
        model=User
        fields="__all__"

class SubsciptionSerializer(ModelSerializer):
    class Meta:
        model=SubscriptionModel
        fields="__all__"

class PlanSerializer(ModelSerializer):
    class Meta:
        model=PlanModel
        fields="__all__"