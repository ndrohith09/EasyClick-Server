from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.utils.translation import gettext_lazy as _

from .models import *
import jwt

from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
import hashlib 
    
def generate_token(payload):
    """
        function to generate authentication token of a user
    """
    dt=timezone.now()+timedelta(days=60)

    payload["exp"]=dt.timestamp()

    return jwt.encode(payload,settings.SECRET_KEY,algorithm="HS256")


def get_request_header(request):
	header=request.META.get('HTTP_AUTHORIZATION','')
	
	return header



class UserAuthentication(BaseAuthentication):
    keyword="Bearer"
    def authenticate(self,request):

        auth=get_request_header(request).split()
        print(auth)
        if not auth or auth[0].lower()!=self.keyword.lower():
            raise exceptions.AuthenticationFailed(_('Not authorised! Token is not provided'))

        print("1")
        print(auth)
        if(len(auth)==1):
            msg = _('Invalid token header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid token header. Token string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        token_=auth[1]

        try:
            # decode_token=jwt.decode(token_,settings.SECRET_KEY,algorithms=['HS256'])

            # if "id" not in decode_token.keys():
            #     raise exceptions.AuthenticationFailed(_('Invalid token.'))
            # id=decode_token["id"]

            user=User.objects.filter(access_token=token_)
            print(user)
            if user.exists():
                return (user[0],None)
            else:
                raise exceptions.AuthenticationFailed(_('Invalid token.'))
        
        except jwt.exceptions.InvalidSignatureError:
            raise exceptions.AuthenticationFailed(_('Invalid token given'))
        
        except jwt.exceptions.DecodeError:
            raise exceptions.AuthenticationFailed(_('Invalid token given'))
        
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed(_('Token expired'))



