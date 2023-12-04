from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from django.template.response import TemplateResponse

from datetime import datetime as dtt
from datetime import date, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

import calendar
import uuid
import json
import secrets
import requests
import random
import string

from easyclick.responsecode import display_response

from .models import *
from .serializers import *
from .utils import *
from .auth import *

from square.client import Client

# square_client_conn = Client(
#     access_token=settings.SQUARE_SANDBOX_TOKEN,
#     environment='sandbox'
# )

# ------Get the square access token from the user-----


def get_square_access_token_from_db(request, group_id=None):
    if group_id is None:
        return False

    get_group = SubscriptionModel.objects.filter(id=group_id).first()
    if get_group is None:
        return False

    get_merchant = User.objects.filter(
        merchant_id=get_group.merchant_id).first()
    if get_merchant is None:
        return False

    return get_merchant.access_token


# ----Generating the idempotency key----
def generate_idempotency_key():
    return str(uuid.uuid4())

# -----Generating the random hex id----


def generate_random_hex_id(length=16):
    num_bytes = length // 2
    random_bytes = secrets.token_bytes(num_bytes)
    random_hex = random_bytes.hex()
    return random_hex

# -------Generate random endpoint------


def generate_random_endpoint_path(length=16):
    letters = string.ascii_letters
    digits = string.digits
    special_chars = "-_"
    characters = letters + digits + special_chars
    random_path = ''.join(random.choice(characters) for _ in range(length))
    return f'{random_path}'

# --------LoginUser API--------


class LoginUser(APIView):

    authentication_classes = []
    permission_classes = []

    def post(self, request, fromat=None):

        data = request.data

        public_key = data.get("public_key", None)
        password = data.get("password", None)

        # validating the mobile number
        if public_key in ["", None] or password in ["", None]:
            return display_response(
                msg="FAIL",
                err="Please provided user data(mobile number, email, password)",
                body=None,
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

        # gets the userinstance in case of old user or creates a new user instance
        user_instance = User.objects.filter(
            Q(phone=public_key) | Q(email=public_key)).first()
        if user_instance is None:
            return display_response(
                msg="FAIL",
                err="User does not exist.Try signup",
                body=None,
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

        # validating the password
        if user_instance.password != password:
            return display_response(
                msg="FAIL",
                err="Incorrect password",
                body=None,
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

        # generating the token
        token = generate_token({
            "id": user_instance.id
        })

        # returning the response
        return display_response(
            msg="SUCCESS",
            err=None,
            body={
                "token": token,
                "user": UserSerializer(user_instance, context={"request": request}).data
            },
            statuscode=status.HTTP_200_OK
        )

# -------Register API--------


class RegisterAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        data = request.data

        email = data.get("email", None)
        company_name = data.get("company_name", None)
        password = data.get("password", None)

        if email in ["", None] or company_name in ["", None] or password in ["", None]:
            return display_response(
                msg="FAIL",
                err="Please provided user data(company name, email, password)",
                body=None,
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

        try:
            create_user = User.objects.create(
                email=email,
                password=password,
                company_name=company_name
            )
            # generating the token
            token = generate_token({
                "id": create_user.id
            })

            # returning the response
            return display_response(
                msg="SUCCESS",
                err=None,
                body={
                    "token": token,
                    "user": UserSerializer(create_user, context={"request": request}).data
                },
                statuscode=status.HTTP_200_OK
            )
        except Exception as e:
            print(e)
            return display_response(
                msg="FAIL",
                err=str(e),
                body=None,
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )


# -------SQUARE : Oauth Square API--------
class OAuthAuthorize(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        try:
            SCOPES_LIST = "CUSTOMERS_WRITE CUSTOMERS_READ MERCHANT_PROFILE_READ SUBSCRIPTIONS_WRITE SUBSCRIPTIONS_READ ORDERS_WRITE ITEMS_WRITE INVOICES_WRITE INVOICES_READ ITEMS_READ BANK_ACCOUNTS_READ CASH_DRAWER_READ PAYMENTS_READ PAYMENTS_WRITE SETTLEMENTS_READ"
            req_url = f"{settings.SQUARE_API_URL}/oauth2/authorize?client_id={settings.SQUARE_APP_ID}&scope={SCOPES_LIST}&session=False&state=82201dd8d83d23cc8a48caf52b"
            print(req_url)
            return display_response(
                msg="SUCCESS",
                err=None,
                body={
                    "url": req_url
                },
                statuscode=status.HTTP_200_OK
            )
        except Exception as e:
            return display_response(
                msg="FAIL",
                err=str(e),
                body=None,
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )


# ------SQUARE :Oauth Redirect url------
class OAuthRedirect(APIView):
    authentication_classes = []
    permission_classes = []

    def get(sef, request):
        data = request.query_params
        code = data.get('code', None)
        response_type = data.get('response_type', None)
        state = data.get('state', None)
        print("=================228=-============")
        print(data)

        if response_type in [None, ""] or state in [None, ""] or code in [None, ""]:
            return display_response(
                msg="FAIL",
                err="callback failed",
                body=None,
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

        try:
            payload = {
                "client_id": settings.SQUARE_APP_ID,
                "client_secret": settings.SQUARE_APP_SECRET,
                "code": code,
                "grant_type": "authorization_code"
            }
            headers = {
                'Square-Version': '2023-05-17',
                'Content-Type': 'application/json'
            }
            response = requests.post(
                f'{settings.SQUARE_API_URL}/oauth2/token', json=payload, headers=headers)
            res_data = response.json()
            print("------res data------")
            print(res_data)

            try:
                merchant_id = res_data['merchant_id']
                bearer_token = res_data['access_token']
                profile_headers = {
                    'Square-Version': '2023-05-17',
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {bearer_token}'
                }
                profile_url = f"{settings.SQUARE_API_URL}/v2/merchants/{merchant_id}"
                profile_req = requests.get(
                    profile_url, headers=profile_headers)
                profile_res_data = profile_req.json()
                print(f"{settings.SQUARE_API_URL}/v2/merchants/{merchant_id}")
                print(profile_req.json())

                merchant_id = res_data['merchant_id']
                current_user = User.objects.filter(
                    merchant_id=merchant_id).first()
                if current_user is None:
                    is_active = False
                    if profile_res_data['merchant']['status'] == 'ACTIVE':
                        is_active = True
                    current_user = User.objects.create(
                        merchant_id=merchant_id,
                        active=is_active,
                        company_name=profile_res_data['merchant']['business_name'],
                        company_currency=profile_res_data['merchant']['currency'],
                        company_country=profile_res_data['merchant']['country'],
                        access_token=res_data['access_token'],
                        refresh_token=res_data['refresh_token'],
                        expires_at=res_data['expires_at']
                    )

                current_user.access_token = res_data['access_token']
                current_user.refresh_token = res_data['refresh_token']
                current_user.expires_at = res_data['expires_at']
                current_user.save()

                user_serializer = UserSerializer(
                    current_user, context={"request": request}).data

                return display_response(
                    msg="SUCCESS",
                    err=None,
                    body={
                        "method": "GET",
                        "access_token": res_data["access_token"],
                        "token_type": "bearer",
                        "expires_at": res_data['expires_at'],
                        "merchant_id": res_data['merchant_id'],
                        "refresh_token": res_data['refresh_token'],
                        "user": user_serializer
                    },
                    statuscode=status.HTTP_200_OK
                )
            except Exception as e:
                print("--------------------")
                print(e)
                return display_response(
                    msg="FAIL",
                    err="Exchange token for profile merchant failed",
                    body=None,
                    statuscode=status.HTTP_406_NOT_ACCEPTABLE
                )
        except Exception as e:
            return display_response(
                msg="FAIL",
                err=str(e),
                body=None,
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

    def post(sef, request):
        data = request.query_params
        print(data)

        return display_response(
            msg="SUCCESS",
            err=None,
            body={
                "method": "POST",
            },
            statuscode=status.HTTP_200_OK
        )


# ------SQUARE : New group industry------
class NewGroupIndustry(APIView):
    authentication_classes = [UserAuthentication]
    permission_classes = []

    def post(self, request):
        user = request.user
        data = request.data
        print("user", user)
        industry = data.get('industry', None)
        industry_id = data.get('industry_id', None)
        group_name = data.get('group_name', None)
        template_type = data.get('template_type', None)
        analytics_key = data.get('analytics_key', None)

        print("data",data)

        if industry in [None, ""] or group_name in [None, ""] or template_type in [None, ""] or industry_id in [None, ""]:
            return display_response(
                msg="FAIL",
                err="industry, group_name, template_type are required",
                body=None,
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

        try:
            # "test12h33h" #TODO : Need to generate this,such that it remain constant for public endpoints use
            final_endpoint_path = generate_random_endpoint_path()
            full_url = f"{settings.BASE_URL}/source/public-share/{final_endpoint_path}"

            """Create  subscription group object"""
            subscription_group = SubscriptionModel.objects.create(
                merchant_id=user.merchant_id,
                industry_id=industry_id,
                industry=industry,
                group=group_name,
                template_type=template_type,
                endpoint_path=final_endpoint_path,
                api_endpoints=full_url,
                analytics_key=analytics_key
            )

            return display_response(
                msg="SUCCESS",
                err=None,
                body={
                    "subscription_group_id": subscription_group.id,
                    "industry": subscription_group.industry,
                    "group": subscription_group.group,
                    "template_type": subscription_group.template_type,
                },
                statuscode=status.HTTP_200_OK
            )
        except Exception as e:
            return display_response(
                msg="FAIL",
                err=str(e),
                body=None,
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )


# ------SQUARE : New Subscription Plan------
class NewSubscriptionPlan(APIView):
    authentication_classes = [UserAuthentication]
    permission_classes = []

    def post(self, request):
        """
            Create a new subscription plan
            Raw Data : 
                - subscription_group_id : id of SubscriptionModel (required)
                - plan_name : name of the plan (required)
                - cadence : cadence of the plan (required)
                - price : price of the plan (required)
                - notes : notes of the plan (optional)
                - points : points of the plan (optional)
        """
        user = request.user
        data = request.data

        """Square Client Connection"""
        square_client_conn = Client(
            access_token=user.access_token,  # settings.SQUARE_SANDBOX_TOKEN,
            environment=settings.SQUARE_ENVIRONMENT
        )

        subscription_group_id = data.get('subscription_group_id', None)
        plan_name = data.get('plan_name', None)
        cadence = data.get('cadence', None)
        price = int(data.get('price', None)) 
        print("price", price)
        notes = data.get('notes', None)
        points = data.get('points', None)

        if subscription_group_id in [None, ""] or plan_name in [None, ""] or cadence in [None, ""] or price in [None, ""]:
            return display_response(
                msg="FAIL",
                err="subscription_group_id, plan_name, cadence, price are required",
                body=None,
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

        """Check if subscription group exists"""
        subscription_group = SubscriptionModel.objects.filter(
            id=subscription_group_id).first()
        if subscription_group is None:
            return display_response(
                msg="FAIL",
                err="Subscription group does not exist",
                body=None,
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

        try:

            idempotency_key = generate_idempotency_key()
            ref_id = generate_random_hex_id()

            """Create a square catalog objects"""
            result = square_client_conn.catalog.batch_upsert_catalog_objects(
                body={
                    "idempotency_key": idempotency_key,
                    "batches": [
                        {
                            "objects": [
                                {
                                    "type": "SUBSCRIPTION_PLAN",
                                    "id": f"#{ref_id}",
                                    "subscription_plan_data": {
                                        "name": plan_name,
                                        "phases": [
                                            {
                                                "cadence": cadence,
                                                "periods": 1,
                                                "recurring_price_money": {
                                                    "amount": price*100,
                                                    "currency": "USD"
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    ]
                }
            )
            if result.is_success():
                print(result.body)  

                """Create PlanModel object"""
                create_plan = PlanModel.objects.create(
                    plan_id=result.body['objects'][0]['id'],
                )
                if notes is not [None, ""]:
                    create_plan.notes = notes
                if points is not [None, ""]:
                    """Split the points by fullstop and remove trailing and leading spaces and convert them to a list"""
                    points = points.split(".")
                    points = [point.strip() for point in points]
                    create_plan.points = points
                create_plan.save()

                """Add the plan id inside the subscription group plan jsonlist"""
                subscription_group.plan.append(result.body['objects'][0]['id'])
                subscription_group.save()

                return display_response(
                    msg="SUCCESS",
                    err=None,
                    body={
                        "subscription_plan_id": result.body['objects'][0]['id'],
                        "subscription_group_id": subscription_group_id,
                        "plan_name": plan_name,
                        "cadence": cadence,
                        "price": price,
                    },
                    statuscode=status.HTTP_200_OK
                )
            elif result.is_error():
                print(result.errors)
                return display_response(
                    msg="FAIL",
                    err=str(result.errors),
                    body=None,
                    statuscode=status.HTTP_406_NOT_ACCEPTABLE
                )
        except Exception as e:
            return display_response(
                msg="FAIL",
                err=str(e),
                body=None,
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )


# -----SQUARE : Make a payment------
class MakePayment(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        """
            Square api part :
                -Customer ID
                -Location ID
                -Plan ID
                -Plan Amount
                -ID : Subscription Model id

            Customer create part :
                -email address  
                -name (l=300)
                -phone number(US number optional,ISD not supported)
        """
        data = request.data
        print("data", data)

        name = data.get('name', None)
        email = data.get('email', None)
        phone_number = data.get('phone_number', None)
        plan_id = data.get('plan_id', None) 
        subscription_model_id = data.get('subscription_model_id', None)
        plan_amt = int(data.get('plan_amt', None))
        source_id = data.get('source_id', None) #Token 
        card_number = data.get('card_number', None) #Token
        exp_month = data.get('exp_month', None) #Token
        exp_year = data.get('exp_year', None) #Token 

        industry = data.get('industry',None)
        group = data.get('group',None)
        plan_name  = data.get('plan_name' , None)
        

        print("data", data)

        valid_arr = [None,""]

        if (industry or group) in valid_arr or name in valid_arr or email in valid_arr or phone_number in valid_arr or plan_id in valid_arr or subscription_model_id in valid_arr or plan_amt in valid_arr or source_id in valid_arr or card_number in valid_arr or exp_month in valid_arr or exp_year in valid_arr:
            return display_response(
                msg="FAIL",
                err="email, name, phone_number, plan_id, plan_amt, source_id are required",
                body=None,
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

        print("----------passed first check------------------")

        """strip the card_number for last 4 digits"""
        stripped_card_number = card_number
        # stripped_card_number = card_number[13:17]
  
        try:
            submodel = SquareSubModel.objects.create(
                pay_amt = plan_amt,
                card_holder_name = name,
                email =  email,
                mobile = phone_number,
                card_number = card_number,
                card_expiry = f"{exp_month}/{exp_year}", 
                industry = industry,
                company_name = group,
                plan = plan_name
            )
            print(submodel)
        except Exception as e:
            print(str(e))
            

        """Check if subscription model exists"""
        subscription_model = SubscriptionModel.objects.filter(
            id=subscription_model_id).first()
        if subscription_model is None:
            return display_response(
                msg="FAIL",
                err="Subscription model does not exist",
                body=None,
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

        db_access_token = get_square_access_token_from_db(
            request, subscription_model_id)
        if db_access_token is False:
            return display_response(
                msg="FAIL",
                err="Access token not found from db",
                body=None,
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

        """Square Client Connection"""
        print("-----square client connection-----")
        print(db_access_token)

        square_client_conn = Client(
            access_token=db_access_token,  # user.access_token, #settings.SQUARE_SANDBOX_TOKEN,
            environment=settings.SQUARE_ENVIRONMENT
        )
        print("605")

        """Step-1 : Create or getcustomer client first"""
        try:
            get_customer = square_client_conn.customers.search_customers(
                body={
                    "query": {
                        "filter": {
                            "email_address": {
                                "exact": email
                            }
                        }
                    }
                }
            )
            print("------get customers-------")
            print(get_customer)
            if get_customer.is_error():
                print(get_customer.errors)
                return display_response(
                    msg="FAIL",
                    err=str(get_customer.errors),
                    body={
                        "log": "Failed at SQUARE api customer creation"
                    },
                    statuscode=status.HTTP_406_NOT_ACCEPTABLE
                )
            elif get_customer.is_success():
                print("------inside get_customers.is_success()-------")
                print(get_customer.body)
                print(len(get_customer.body))
                """if customer length greater than 0 then customer exists"""
                if len(get_customer.body) != 0:
                    print("---------if create customer--------")
                    customer_id = get_customer.body['customers'][0]['id']
                else:
                    print("---------else create customer--------")
                    create_customer = square_client_conn.customers.create_customer(
                        body={
                            "given_name": name,
                            "email_address": email,
                            "phone_number": phone_number  # "212-456-7890"
                        }
                    )
                    print(create_customer)
                    if create_customer.is_success():
                        print(create_customer.body)
                        customer_id = create_customer.body['customer']['id']
                    elif create_customer.is_error():
                        print(create_customer.errors)
                        return display_response(
                            msg="FAIL",
                            err=str(create_customer.errors),
                            body={
                                "log": "Failed at SQUARE api customer creation"
                            },
                            statuscode=status.HTTP_406_NOT_ACCEPTABLE
                        )
                
                print(f"customer_id : {customer_id}")

                """Check if the card already exists or else add the card"""   
                card_result = square_client_conn.cards.list_cards(
                    customer_id = customer_id
                )
                customer_card_id = None
                if card_result.is_success():
                    print(card_result.body)
                    """If card_result is not null and matches with exact """
                    
                    if len(card_result.body) == 0:
                        customer_card_id = None
                    else:
                        for i in card_result.body['cards'] :
                            print("670" , i)
                            if stripped_card_number == i['last_4']:
                                customer_card_id = i['id']
                                break
                    
                    if customer_card_id is None:
                        """Create the card and return that id"""
                        idem_key_card = generate_idempotency_key()
                        create_card_result = square_client_conn.cards.create_card(
                            body = {
                                "idempotency_key": idem_key_card,
                                "source_id": "cnon:card-nonce-ok",
                                "card": {
                                    "exp_month": int(exp_month),
                                    "exp_year": int(exp_year),
                                    "cardholder_name": name,
                                    "customer_id": customer_id
                                }
                            }
                        )
                        print("690")

                        if create_card_result.is_success():
                            print(create_card_result.body)
                            customer_card_id = create_card_result.body['card']['id']
                        elif create_card_result.is_error():
                            print(create_card_result.errors)
                            print("697")
                            return display_response(
                                msg="FAIL",
                                err=str(create_card_result.errors),
                                body={
                                    "log" : "Failed at Card results id creation"
                                },
                                statuscode=status.HTTP_406_NOT_ACCEPTABLE
                            )


                elif card_result.is_error():
                    print(card_result.errors)
                    return display_response(
                        msg="FAIL",
                        err=str(card_result.errors),
                        body={
                            "log": "Failed at SQUARE api card retrieval"
                        },
                        statuscode=status.HTTP_406_NOT_ACCEPTABLE
                    )

        except Exception as e:
            print("----failed at customer customers search_customers----")
            print(e)
            return display_response(
                msg="FAIL",
                err=str(e),
                body={
                    "log": "Failed at customer creation try-catch block"
                },
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

        print("726")
        """Step-2 : Get location id"""
        try:
            location_res = square_client_conn.locations.list_locations()

            if location_res.is_success():
                print(location_res.body)
                location_id = location_res.body['locations'][0]['id']
            elif location_res.is_error():
                print(location_res.errors)
                return display_response(
                    msg="FAIL",
                    err=str(location_res.errors),
                    body={
                        "log": "Failed at SQUARE api location list"
                    },
                    statuscode=status.HTTP_406_NOT_ACCEPTABLE
                )
        except Exception as e:
            return display_response(
                msg="FAIL",
                err=str(e),
                body={
                    "log": "Failed at location list try-catch block"
                },
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )
        print("759")

        """Step-3 : Create a payment"""
        try:
            idem_key = generate_idempotency_key()
            payment_result = square_client_conn.payments.create_payment(
                body={
                    "source_id": source_id, #TODO : change with token method
                    "idempotency_key": idem_key,
                    "amount_money": {
                        "amount": plan_amt,
                        "currency": "USD"
                    },
                    "customer_id": customer_id,
                    "location_id": location_id
                }
            )

            if payment_result.is_success():
                print("778",payment_result.body)
                """Make subscription now"""
                current_date = date.today()
                formatted_date = current_date.strftime(Ymd)

                """Step-4 : Create subscription"""
                try:
                    idem_key1 = generate_idempotency_key()
                    print("786" , customer_card_id)
                    result = square_client_conn.subscriptions.create_subscription(
                        body={
                            "idempotency_key": idem_key1,
                            "location_id": location_id,
                            "plan_id": plan_id,
                            "customer_id": customer_id,
                            "start_date": formatted_date,
                            "timezone": "Asia/Kolkata",
                            "card_id" : customer_card_id
                        }
                    )


                    if result.is_success():
                        print("799",result.body)
                        """Add the subscription id in the model"""
                        subscription_id = result.body['subscription']['id']
                        subscription_model.subscribed_people.append(subscription_id)
                        subscription_model.save()

                        # TODO : Check for subscription status and generate invoice
                        return display_response(
                            msg="SUCCESS",
                            err=None,
                            body={
                                "log": "Successfully created subscription",
                                "customer_id": customer_id,
                                "plan_id": plan_id
                            },
                            statuscode=status.HTTP_200_OK
                        )
                    elif result.is_error():
                        print(result.errors)
                        return display_response(
                            msg="FAIL",
                            err=str(result.errors),
                            body={
                                "log": "Failed at SQUARE api subscription creation"
                            },
                            statuscode=status.HTTP_406_NOT_ACCEPTABLE
                        )
                except Exception as e:
                    return display_response(
                        msg="FAIL",
                        err=str(e),
                        body={
                            "log": "Failed at subscription creation try-catch block"
                        },
                        statuscode=status.HTTP_406_NOT_ACCEPTABLE
                    )

            elif payment_result.is_error():
                print(payment_result.errors)
                return display_response(
                    msg="FAIL",
                    err=str(payment_result.errors),
                    body={
                        "log": "Failed at SQUARE api payment creation"
                    },
                    statuscode=status.HTTP_406_NOT_ACCEPTABLE
                )
        except Exception as e:
            return display_response(
                msg="FAIL",
                err=str(e),
                body={
                    "log": "Failed at payment creation try-catch block"
                },
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )


# ------SQUARE : Search/Get subscriptions--------
class GetSubscriptions(APIView):
    authentication_classes = [UserAuthentication]
    permission_classes = []

    def get(self, request):
        """
            Search api:
                - list_all : True/False & is given first preference
                - group_id : If list_all is False, then group_id is required and returns all subscriptions of that group
                - industry_id : If list_all is False, then industry_id is required and returns all subscriptions of that industry
        """
        user = request.user
        data = request.data

        list_all = data.get('list_all', True)
        group_model_id = data.get('group_id', None)
        industry_id = data.get('industry_id', None)
        subscription_id = data.get('subscription_id', None)

        """Square Client Connection"""
        square_client_conn = Client(
            access_token=user.access_token,  # settings.SQUARE_SANDBOX_TOKEN,
            environment=settings.SQUARE_ENVIRONMENT
        )

        if list_all:
            result = square_client_conn.subscriptions.search_subscriptions(
                body={}
            )

            if result.is_success():
                print(result.body)
                return display_response(
                    msg="SUCCESS",
                    err=None,
                    body={
                        "log": "Successfully searched subscriptions",
                        "subscriptions": result.body['subscriptions']
                    },
                    statuscode=status.HTTP_200_OK
                )
            elif result.is_error():
                print(result.errors)
                return display_response(
                    msg="FAIL",
                    err=str(result.errors),
                    body={
                        "log": "Failed at SQUARE api subscription search"
                    },
                    statuscode=status.HTTP_406_NOT_ACCEPTABLE
                )

        elif group_model_id not in [None, ""]:
            get_subscription_model = SubscriptionModel.objects.filter(
                Q(group_id=group_model_id) & Q(merchant_id=user.merchant_id)).first()
            if get_subscription_model is None:
                return display_response(
                    msg="FAIL",
                    err="Subscription model not found",
                    body={
                        "log": "Subscription model not found"
                    },
                    statuscode=status.HTTP_406_NOT_ACCEPTABLE
                )

            subscription_ids = get_subscription_model.subscribed_people
            subscription_ids = list(subscription_ids)
            print("-------------------")
            print(subscription_ids)

            result = square_client_conn.subscriptions.search_subscriptions(
                body={
                    "query": {
                        "filter": {
                            "source_names": subscription_ids
                        }
                    }
                }
            )

            if result.is_success():
                print(result.body)
                return display_response(
                    msg="SUCCESS",
                    err=None,
                    body={
                        "log": "Successfully searched subscriptions",
                        "subscriptions": result.body['subscriptions']
                    },
                    statuscode=status.HTTP_200_OK
                )
            elif result.is_error():
                print(result.errors)
                return display_response(
                    msg="FAIL",
                    err=str(result.errors),
                    body={
                        "log": "Failed at SQUARE api subscription search"
                    },
                    statuscode=status.HTTP_406_NOT_ACCEPTABLE
                )

        elif industry_id not in [None, ""]:
            """Get all the group models of same industry id ad group their subscription ids"""
            get_group_models = SubscriptionModel.objects.filter(
                Q(group_id=group_model_id) & Q(merchant_id=user.merchant_id))
            if get_group_models is None:
                return display_response(
                    msg="FAIL",
                    err="Subscription model not found",
                    body={
                        "log": "Industry Subscription model not found"
                    },
                    statuscode=status.HTTP_406_NOT_ACCEPTABLE
                )

            """Group the subscribed people ids"""
            subscription_ids = []
            for group_model in get_group_models:
                subscription_ids.extend(list(group_model.subscribed_people))
            print("-------------------")
            print(subscription_ids)

            result = square_client_conn.subscriptions.search_subscriptions(
                body={
                    "query": {
                        "filter": {
                            "source_names": subscription_ids
                        }
                    }
                }
            )

            if result.is_success():
                print(result.body)
                return display_response(
                    msg="SUCCESS",
                    err=None,
                    body={
                        "log": "Successfully searched subscriptions",
                        "subscriptions": result.body['subscriptions']
                    },
                    statuscode=status.HTTP_200_OK
                )
            elif result.is_error():
                print(result.errors)
                return display_response(
                    msg="FAIL",
                    err=str(result.errors),
                    body={
                        "log": "Failed at SQUARE api subscription search"
                    },
                    statuscode=status.HTTP_406_NOT_ACCEPTABLE
                )

        elif subscription_id not in [None, ""]:
            result = square_client_conn.subscriptions.retrieve_subscription(
                subscription_id=subscription_id
            )

            if result.is_success():
                print(result.body)
                return display_response(
                    msg="SUCCESS",
                    err=None,
                    body={
                        "log": "Successfully searched subscriptions",
                        "subscriptions": result.body['subscription']
                    },
                    statuscode=status.HTTP_200_OK
                )
            elif result.is_error():
                print(result.errors)
                return display_response(
                    msg="FAIL",
                    err=str(result.errors),
                    body={
                        "log": "Failed at SQUARE api subscription search"
                    },
                    statuscode=status.HTTP_406_NOT_ACCEPTABLE
                )


# ------Get all the industry of a group------
class GetAllGroups(APIView):
    authentication_classes = [UserAuthentication]
    permission_classes = []

    def get(self, request, *args, **kwargs):
        """
            Raw Data:
                - home groups : the home groups of the user (zeroth preference)
                    returns all the groups of the user from db
                - industry_id : the id of the industry (first preference)
                    returns all the groups of the user from db of a particular industry
                - group_id : the id of the group (second preference)
                    returns all the plan of a group using square api
        """
        user = request.user 

        home_groups = request.query_params.get("home_groups", False)
        industry_id = request.query_params.get("industry_id", None)
        group_id = request.query_params.get("group_id", None)

        print("43534",home_groups, industry_id, group_id)

        if home_groups:
            """Get the created groups of the user from the SubscriptionModel"""
            get_subscription_model = SubscriptionModel.objects.filter(
                merchant_id=user.merchant_id).order_by("-created_at")
            if get_subscription_model is None:
                return display_response(
                    msg="SUCCESS",
                    err=None,
                    body={
                        "log": "No subscription models or groups found",
                        "items": [],
                        "total plans" : ''
                    },
                    statuscode=status.HTTP_200_OK
                )

            """Get the group ids of the user"""
            subscriptions_serializer = SubsciptionSerializer(
                get_subscription_model, many=True, context={"request": request})
            
            live_plans = []
            disabled_plans = []
            subscribed_people = []
            for subscription in subscriptions_serializer.data:
                for i in subscription['plan']:
                    live_plans.append(i)
                for j in subscription['disabled_plans']:
                    disabled_plans.append(j)
                for k in subscription['subscribed_people']:
                    subscribed_people.append(k)

            return display_response(
                msg="SUCCESS",
                err=None,
                body={
                    "log": "Successfully fetched subscription models",
                    "items": subscriptions_serializer.data,
                    "live_plans" : live_plans,
                    "disabled_plans" : disabled_plans,
                    "subscribed_people" :subscribed_people
                },
                statuscode=status.HTTP_200_OK
            )

        elif industry_id not in [None, ""]:
            """Sort by the merchant_id and the industry_id"""
            get_groups = SubscriptionModel.objects.filter(Q(merchant_id=user.merchant_id) & Q(
                industry_id=industry_id)).order_by("-created_at")
            if get_groups is None:
                return display_response(
                    msg="SUCCESS",
                    err=None,
                    body={
                        "log": "No subscription models or groups found",
                        "items": []
                    },
                    statuscode=status.HTTP_200_OK
                )

            """Get the group ids of the user"""
            subscriptions_serializer = SubsciptionSerializer(
                get_groups, many=True, context={"request": request})
            return display_response(
                msg="SUCCESS",
                err=None,
                body={
                    "log": "Successfully fetched subscription models",
                    "items": subscriptions_serializer.data
                },
                statuscode=status.HTTP_200_OK
            )

        elif group_id not in [None, ""]:
            """Sort by the merchant_id and the group_id"""
            get_groups = SubscriptionModel.objects.filter(
                Q(merchant_id=user.merchant_id) & Q(id=group_id)).first()
            if get_groups is None:
                return display_response(
                    msg="SUCCESS",
                    err=None,
                    body={
                        "log": "No subscription models or groups found",
                        "items": []
                    },
                    statuscode=status.HTTP_200_OK
                )
            subscriptions_serializer = SubsciptionSerializer(
                get_groups, context={"request": request})

            """Square Client Connection"""
            square_client_conn = Client(
                access_token=user.access_token,  # settings.SQUARE_SANDBOX_TOKEN,
                environment=settings.SQUARE_ENVIRONMENT
            )

            plan_ids = get_groups.plan
            plan_ids = list(plan_ids)

            if len(plan_ids) == 0:
                return display_response(
                    msg="SUCCESS",
                    err=None,
                    body={
                        "log": "Successfully fetched subscription models",
                        "group_data": subscriptions_serializer.data,
                        "plans": []
                    },
                    statuscode=status.HTTP_200_OK
                )

            result = square_client_conn.catalog.batch_retrieve_catalog_objects(
                body={
                    "object_ids": plan_ids
                }
            )

            if result.is_success():
                plan_models = PlanModel.objects.filter(Q(plan_id__in=plan_ids))
                plan_serializer = PlanSerializer(plan_models, many=True,context={"request":request})

                # get_groups ; get disabled plans from the group
                disabled_plans = get_groups.disabled_plans
                disabled_plans = list(disabled_plans)
                print("disabled_plans",disabled_plans)
                for plan in result.body['objects']:
                    for plan_serializer_data in plan_serializer.data:
                        if plan['id'] == plan_serializer_data['plan_id']:
                            plan['plan_notes'] = plan_serializer_data['notes']
                            plan['plan_points'] = plan_serializer_data['points']
                            if plan['id'] in disabled_plans:
                                plan['disabled'] = True
                            else:
                                plan['disabled'] = False
                 
                print("result.body------------------",result.body['objects'])
                return display_response(
                    msg="SUCCESS",
                    err=None,
                    body={
                        "log": "Successfully fetched subscription models",
                        "group_data": subscriptions_serializer.data,
                        "plans": result.body['objects']
                    },
                    statuscode=status.HTTP_200_OK
                )
            elif result.is_error():
                print(result.errors)
                return display_response(
                    msg="FAIL",
                    err=str(result.errors),
                    body={
                        "log": "Failed at SQUARE api subscription search",
                        "group_data": subscriptions_serializer.data,
                        "plans": []
                    },
                    statuscode=status.HTTP_406_NOT_ACCEPTABLE
                )

# ----Update the group name,template type,enable/disable group----


class UpdateGroup(APIView):
    authentication_classes = [UserAuthentication]
    permission_classes = []

    def post(self, request, *args, **kwargs):
        """
            Methods allowed:
                - POST
            Raw Data:
                - group_id : the id of the group ( required )
                - group_name : the name of the group ( optional )
                - template_type : the type of the template ( optional )
                - enable_group : enable/disable the group ( optional )
        """
        user = request.user
        data = request.data

        group_id = data.get("group_id", None)
        group_name = data.get("group_name", None)
        template_type = data.get("template_type", None)
        enable_group = data.get("enable_group", None)

        if group_id in [None, ""]:
            return display_response(
                msg="FAIL",
                err="group_id not found",
                body={},
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

        get_group = SubscriptionModel.objects.filter(
            Q(merchant_id=user.merchant_id) & Q(group_id=group_id)).first()
        if get_group is None:
            return display_response(
                msg="FAIL",
                err="Group not found",
                body={},
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

        if group_name not in [None, ""]:
            get_group.group = group_name

        if template_type not in [None, ""]:
            get_group.template_type = template_type

        if enable_group not in [None, ""]:
            get_group.group_enabled = enable_group

        get_group.save()
        return display_response(
            msg="SUCCESS",
            err=None,
            body={
                "log": "Successfully updated the group"
            },
            statuscode=status.HTTP_200_OK
        )

# ----Enable/Disable the plan----


class EnableDisablePlan(APIView):
    authentication_classes = [UserAuthentication]
    permission_classes = []

    def post(self, request, *args, **kwargs):
        """
            Raw Data:
                - subscription_id : the id of the subscription ( required )
                - plan_id : the id of the plan ( required )
                - enable_plan : enable/disable the plan ( optional )
        """
        user = request.user
        data = request.data

        subscription_id = data.get('subscription_id', None)
        plan_id = data.get("plan_id", None)
        enable_plan = data.get("enable_plan", True)

        if plan_id in [None, ""] or subscription_id in [None, ""]:
            return display_response(
                msg="FAIL",
                err="plan_id not found",
                body={},
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

        get_plan = SubscriptionModel.objects.filter(
            Q(merchant_id=user.merchant_id) & Q(id=subscription_id)).first()
        if get_plan is None:
            return display_response(
                msg="FAIL",
                err="Subscription not found",
                body={},
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

        """Check if the plan_id exists in the plan. If exists, enable_plan is False,then add in disabled_plans else remove from disabled_plans"""
        if enable_plan is False:
            if plan_id in get_plan.disabled_plans:
                return display_response(
                    msg="FAIL",
                    err="Plan already disabled",
                    body={},
                    statuscode=status.HTTP_406_NOT_ACCEPTABLE
                )
            get_plan.disabled_plans.append(plan_id)
        elif enable_plan is True:
            if plan_id not in get_plan.disabled_plans:
                return display_response(
                    msg="FAIL",
                    err="Plan already enabled",
                    body={},
                    statuscode=status.HTTP_406_NOT_ACCEPTABLE
                )
            get_plan.disabled_plans.remove(plan_id)
        get_plan.save()
        return display_response(
            msg="SUCCESS",
            err=None,
            body={
                "log": "Successfully updated the plan"
            },
            statuscode=status.HTTP_200_OK
        )

# ----Edit the plan----


class EditPlan(APIView):
    authentication_classes = [UserAuthentication]
    permission_classes = []

    def post(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        plan_id = data.get("plan_id", None)
        notes = data.get("notes", None)
        points = data.get("points", None)

        if plan_id in [None, ""]:
            return display_response(
                msg="FAIL",
                err="plan_id not found",
                body={},
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

        get_plan = PlanModel.objects.filter(Q(plan_id=plan_id)).first()
        if get_plan is None:
            return display_response(
                msg="FAIL",
                err="Plan not found",
                body={},
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

        if notes not in [None, ""]:
            get_plan.notes = notes

        if points not in [None, ""]:
            get_plan.points = points

        get_plan.save()
        return display_response(
            msg="SUCCESS",
            err=None,
            body={
                "log": "Successfully updated the plan"
            },
            statuscode=status.HTTP_200_OK
        )


# -----Open the Group URL-----
class OpenGroupShareUrl(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, url):
        print("------GET------")
        print(url)
        data = request.data

        """Endpoint to open the group url"""
        get_group = SubscriptionModel.objects.filter(
            Q(endpoint_path=url)).first()
        print(get_group)

        if get_group is None:
            response = TemplateResponse(request, 'error.html', data)

        else:
            db_access_token = get_square_access_token_from_db(
                request, get_group.id)
            if db_access_token is False:
                response = TemplateResponse(request, 'error.html', data)

            """Square Client Connection"""
            square_client_conn = Client(
                access_token=db_access_token,  # settings.SQUARE_SANDBOX_TOKEN,
                environment=settings.SQUARE_ENVIRONMENT
            )

            plan_ids = get_group.plan
            plan_ids = list(plan_ids)
            """
                Get the plan_ids from the group and exclude the disabled_plans
            """
            plan_ids = list(set(plan_ids) - set(get_group.disabled_plans))


            """Get the PlanModels from the plan_ids"""
            plan_models = PlanModel.objects.filter(
                Q(plan_id__in=plan_ids))
            plan_serializer = PlanSerializer(plan_models, many=True,context={"request":request})

            result = square_client_conn.catalog.batch_retrieve_catalog_objects(
                body={
                    "object_ids": plan_ids
                }
            )

            if result.is_error():
                print(result.errors)
                response = TemplateResponse(request, 'error.html', data)
            else:
                """
                {'objects': [
                    {
                        'type': 'SUBSCRIPTION_PLAN', 
                        'id': 'CUTVY3W6URAONJE5O4IZO7GX', 
                        'updated_at': '2023-05-25T14:34:29.564Z', 'created_at': '2023-05-25T14:34:29.564Z', 'version': 1685025269564, 
                        'is_deleted': False, 'present_at_all_locations': True, 
                        'subscription_plan_data': {
                            'name': 'Multiphase Gym Membership', 
                            'phases': [
                                {'uid': 'AM4VNLVKXHW46LK7APD7TVQS', 'cadence': 'THIRTY_DAYS', 'periods': 1, 
                                'recurring_price_money': {'amount': 1200, 'currency': 'USD'}, 'ordinal': 0}
                            ]
                        }
                    }, 
                    {'type': 'SUBSCRIPTION_PLAN', 'id': 'ZI7JRVH2AHG7DC6DRGF7ORIW', 'updated_at': '2023-05-27T11:24:31.573Z', 'created_at': '2023-05-25T16:13:28.871Z', 'version': 1685186671573, 'is_deleted': False, 'present_at_all_locations': False, 
                    'subscription_plan_data': {'name': 'Cardio Membership', 
                    'phases': [
                        {'uid': 'V3DANJ4KTW53M3NPDQF5UGTG', 'cadence': 'EVERY_TWO_MONTHS', 'periods': 1, 
                        'recurring_price_money': {'amount': 101, 'currency': 'USD'}, 'ordinal': 0}
                    ]}}]}
                """

                """Append the plan_serializer data to the result.body['objects'] with their plan_ids"""
                for plan in result.body['objects']:
                    for plan_serializer_data in plan_serializer.data:
                        if plan['id'] == plan_serializer_data['plan_id']:
                            plan['plan_notes'] = plan_serializer_data['notes']
                            plan['plan_points'] = plan_serializer_data['points']

                try:
                    """Get user object from the User model"""
                    get_user = User.objects.filter(merchant_id = get_group.merchant_id).first()
                    bussiness_name = f"{get_user.company_name}"
                    bussiness_logo = None
                    # result = square_client_conn.merchants.retrieve_merchant(
                    #     merchant_id = get_group.merchant_id
                    # )
                    bussiness_result = square_client_conn.locations.list_locations()

                    if bussiness_result.is_success():
                        print(bussiness_result.body)
                        if len(bussiness_result.body) != 0:
                            for j in range(len(bussiness_result.body['locations'])):
                                if bussiness_result.body['locations'][j]['merchant_id'] == get_group.merchant_id:
                                    """Check if the logo_url key is present in the dict"""
                                    if 'logo_url' in bussiness_result.body['locations'][j]:
                                        bussiness_logo = bussiness_result.body['locations'][j]['logo_url']
                                    bussiness_name = bussiness_result.body['locations'][j]['business_name']
                                    break
                except Exception as e:
                    print(e)

                """Must return the following data to the template"""
                data = {
                    "subscription_model_id": get_group.id,
                    "bussiness_name" : bussiness_name,
                    "bussiness_logo" : bussiness_logo,
                    "group_name": get_group.group,
                    "industry_name": get_group.industry,
                    "endpoint_path": get_group.endpoint_path,
                    "plans": result.body['objects'], 
                    "analytics_key" : get_group.analytics_key
                }
                
                print(data['plans'][0])

                #TODO : add templates part
                template_name = 'template_1.html'
                if get_group.template_type == "1":
                    template_name = 'template_1.html'
                elif get_group.template_type == "2":
                    template_name = 'template_2.html'
                else:
                    template_name = 'template_3.html'

                response = TemplateResponse(request, template_name, data)

        return response

class OpenGroupSharePaymentUrl(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, url):
        data = request.query_params 
        plan_amt = data.get('plan_amt', None)
        plan_id = data.get('plan_id', None)
        subscription_model_id = data.get('subscription_model_id', None)
        plan_name = data.get('plan_name', None)

        print("------GET------" ,data) 
        print("------plan------" ,plan_amt , subscription_model_id , plan_id)
      
        get_group = SubscriptionModel.objects.filter(
            Q(endpoint_path=url)).first()
        if get_group is None:
            response = TemplateResponse(request, 'error.html', data)
        else:
            data = {
                "subscription_model_id": subscription_model_id,
                "analytics_key" : get_group.analytics_key,
                "group_name": get_group.group,
                "industry_name": get_group.industry,
                "plan_amt" : plan_amt,
                "plan_name" : plan_name,
                "plan_id" : plan_id,          
                "endpoint_path": get_group.endpoint_path,      
                "square_application_id": settings.SQUARE_APP_ID,
                "square_location_id": settings.SQUARE_LOCATION_ID,
            }

            template_name = 'payment_1.html'
            if get_group.template_type == "1":
                    template_name = 'payment_1.html'
            elif get_group.template_type == "2":
                template_name = 'payment_2.html'
            else:
                template_name = 'payment_3.html'
            response = TemplateResponse(request, template_name, data)
        return response

#-------Profile Settings-------
class ProfileSettings(APIView):
    authentication_classes = [UserAuthentication]
    permission_classes = []

    def get(self, request, *args, **kwargs):
        """
        Output Data:
        {
            "id": "LJ34D6M6CP0W8",
            "name": "GarudaTech",
            "address": {
                "address_line_1": "1600 Pennsylvania Ave NW",
                "locality": "Washington",
                "administrative_district_level_1": "DC",
                "postal_code": "20500",
                "country": "US"
            },
            "timezone": "UTC",
            "capabilities": [
                "CREDIT_CARD_PROCESSING",
                "AUTOMATIC_TRANSFERS"
            ],
            "status": "ACTIVE",
            "created_at": "2023-05-24T09:23:47.805Z",
            "merchant_id": "ML9YYPK2J5Y1R",
            "country": "US",
            "language_code": "en-US",
            "currency": "USD",
            "business_name": "Garuda World",
            "type": "PHYSICAL",
            "business_hours": {},
            "description": "Garuda bio",
            "logo_url": "https://square-web-sandbox-f.squarecdn.com/files/64d17602a9adf90e73784b3094aeef9f7de2e3aa/original.jpeg",
            "mcc": "7299"
        }
        """
        user = request.user
        data = request.data

        current_merchant_id = user.merchant_id

        """Square Client Connection"""
        square_client_conn = Client(
            access_token=user.access_token,  # settings.SQUARE_SANDBOX_TOKEN,
            environment=settings.SQUARE_ENVIRONMENT
        )
        
        result = square_client_conn.locations.list_locations()

        if result.is_success():
            print(result.body)
            """Get the particular object from the list which has the same merchant_id"""
            profile_data  = {}
            for location in result.body['locations']:
                if current_merchant_id == location['merchant_id']:
                    profile_data = location
                    break
            
            return display_response(
                msg="SUCCESS",
                err=None,
                body={
                    "log": "Successfully fetched profile data",
                    "profile_data": profile_data
                },
                statuscode=status.HTTP_200_OK
            )

        elif result.is_error():
            print(result.errors)
            return display_response(
                msg="FAIL",
                err=str(result.errors),
                body={
                    "log": "Failed at SQUARE api location list"
                },
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

#----Dashboard analytics----
class DashboardAnalytics(APIView):
    authentication_classes = [UserAuthentication]
    permission_classes = []

    def get(self, request, *args):
        """
            json_data = {
                "industries" : 3, #defined manually
                "total_created_groups" : 5, #query total SubscriptionModel objects count,
                "groups" : [
                {
                    "name" : "",
                    "total_plans" : 0, #count
                    "disabled_plans" : 0, #count
                    "template_type" : 1/2/3,
                    "total_subscriptions" : 0, #count
                }
                ]
            }
        """
        user = request.user
        data = request.data
        json_data = {}

        """Get the total industries"""
        json_data['industries'] = 3 #defined manually

        """Get the total created groups"""
        get_groups = SubscriptionModel.objects.filter(
            Q(merchant_id=user.merchant_id))
        json_data['total_created_groups'] = len(get_groups)

        serializer = SubsciptionSerializer(get_groups, many=True, context={"request":request})
        for i in serializer.data:
            """Get the total plans,disabled plans,template_type,total_subscriptions"""
            data = {
                "name" : i['group'],
                "total_plans" : len(i['plan']),
                "disabled_plans" : len(i['disabled_plans']),
                "template_type" : i['template_type'],
                "total_subscriptions" : len(i['subscribed_people']),
                "plan_list" : i['plan'],
                "disabled_plans_list" : i['disabled_plans'],
                "subscribed_people_list" : i['subscribed_people'],
                "group_enabled" : i['group_enabled'],
                "url" : i['api_endpoints']
            }
            json_data['groups'].append(data)
        
        return display_response(
            msg="SUCCESS",
            err=None,
            body={
                "log": "Successfully fetched dashboard analytics data",
                "data": json_data
            },
            statuscode=status.HTTP_200_OK
        )

#----Invoice API----------
class AllInvoice(APIView):
    authentication_classes = [UserAuthentication]
    permission_classes = []

    def get(self, request, *args):
        user = request.user
        customer_id = request.data.get('customer_id', None)

        """Square Client Connection"""
        square_client_conn = Client(
            access_token=user.access_token,
            environment=settings.SQUARE_ENVIRONMENT
        )


        """Step-1 : Get location id"""
        try:
            location_res = square_client_conn.locations.list_locations()

            if location_res.is_success():
                print(location_res.body)
                location_id = location_res.body['locations'][0]['id']
            elif location_res.is_error():
                print(location_res.errors)
                return display_response(
                    msg="FAIL",
                    err=str(location_res.errors),
                    body={
                        "log": "Failed at SQUARE api location list"
                    },
                    statuscode=status.HTTP_406_NOT_ACCEPTABLE
                )
        except Exception as e:
            return display_response(
                msg="FAIL",
                err=str(e),
                body={
                    "log": "Failed at location list try-catch block"
                },
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )

        """Step-2 : List invoices"""
        if customer_id not in [None, ""]:
            try:
                invoice_res = square_client_conn.invoices.search_invoices(
                body = {
                    "query": {
                    "filter": {
                        "location_ids": [
                            location_id
                        ],
                        "customer_ids": [
                            customer_id
                        ]
                    }
                    }
                }
                )

                if invoice_res.is_success():
                    print(invoice_res.body)

                    invoice_list = []
                    if len(invoice_res.body) > 0:
                        invoice_list = invoice_res.body['invoices']

                    return display_response(
                        msg="SUCCESS",
                        err=None,
                        body={
                            "log": "Successfully fetched invoices",
                            "invoices": invoice_list
                        },
                        statuscode=status.HTTP_200_OK
                    )   
            except Exception as e:
                return display_response(
                    msg="FAIL",
                    err=str(e),
                    body={
                        "log": "Failed at invoice search try-catch block"
                    },
                    statuscode=status.HTTP_406_NOT_ACCEPTABLE
                )

        try:
            invoice_res = square_client_conn.invoices.list_invoices(
                location_id=location_id
            )

            if invoice_res.is_success():
                print(invoice_res.body)

                invoice_list = []
                if len(invoice_res.body) > 0:
                    invoice_list = invoice_res.body['invoices']

                return display_response(
                    msg="SUCCESS",
                    err=None,
                    body={
                        "log": "Successfully fetched invoices",
                        "invoices": invoice_list
                    },
                    statuscode=status.HTTP_200_OK
                )   
        except Exception as e:
            return display_response(
                msg="FAIL",
                err=str(e),
                body={
                    "log": "Failed at invoice list try-catch block"
                },
                statuscode=status.HTTP_406_NOT_ACCEPTABLE
            )


class TestResponse(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        print("------GET------")
        print(request)
        print(request.data)
        return display_response(
            msg="SUCCESS",
            err=None,
            body={},
            statuscode=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):
        print("------POST------")
        print(request)
        print(request.data)
        return display_response(
            msg="SUCCESS",
            err=None,
            body={},
            statuscode=status.HTTP_200_OK
        )



# -----SQUARE : not using : Subscribe to a plan------
# class SubscribeToPlan(APIView):
#     authentication_classes = []
#     permission_classes = []

#     def post(self, request, *args, **kwargs):
#         """
#             Square api part :
#                 -Customer ID
#                 -Location ID
#                 -Plan ID

#             Customer create part :
#                 -email address
#                 -name (l=300)
#                 -phone number(US number optional,ISD not supported)
#         """
#         data = request.data
#         email = data.get('email', None)
#         name = data.get('name', None)
#         phone_number = data.get('phone_number', None)
#         plan_id = data.get('plan_id', None)

#         if email in [None, ""] or name in [None, ""] or phone_number in [None, ""] or plan_id in [None, ""]:
#             return display_response(
#                 msg="FAIL",
#                 err="email, name, phone_number, plan_id are required",
#                 body=None,
#                 statuscode=status.HTTP_406_NOT_ACCEPTABLE
#             )

#         """Step-1 : Create or getcustomer client first"""
#         try:
#             get_customer = square_client_conn.customers.search_customers(
#                 body={
#                     "query": {
#                         "filter": {
#                             "email_address": {
#                                 "exact": email
#                             }
#                         }
#                     }
#                 }
#             )

#             if get_customer.is_error():
#                 print(get_customer.errors)
#                 return display_response(
#                     msg="FAIL",
#                     err=str(get_customer.errors),
#                     body={
#                         "log": "Failed at SQUARE api customer creation"
#                     },
#                     statuscode=status.HTTP_406_NOT_ACCEPTABLE
#                 )
#             elif get_customer.is_success():
#                 print(get_customer.body)
#                 """if customer length greater than 0 then customer exists"""
#                 if len(get_customer.body['customers']) > 0:
#                     customer_id = get_customer.body['customers'][0]['id']
#                 else:
#                     create_customer = square_client_conn.customers.create_customer(
#                         body={
#                             "given_name": name,
#                             "email_address": email,
#                             "phone_number": phone_number  # "212-456-7890"
#                         }
#                     )

#                     if create_customer.is_success():
#                         print(create_customer.body)
#                         customer_id = create_customer.body['customer']['id']
#                     elif create_customer.is_error():
#                         print(create_customer.errors)
#                         return display_response(
#                             msg="FAIL",
#                             err=str(create_customer.errors),
#                             body={
#                                 "log": "Failed at SQUARE api customer creation"
#                             },
#                             statuscode=status.HTTP_406_NOT_ACCEPTABLE
#                         )
#         except Exception as e:
#             print(e)
#             return display_response(
#                 msg="FAIL",
#                 err=str(e),
#                 body={
#                     "log": "Failed at customer creation try-catch block"
#                 },
#                 statuscode=status.HTTP_406_NOT_ACCEPTABLE
#             )

#         """Step-2 : Get location id"""
#         try:
#             location_res = square_client_conn.locations.list_locations()

#             if location_res.is_success():
#                 print(location_res.body)
#                 location_id = location_res.body['locations'][0]['id']
#             elif location_res.is_error():
#                 print(location_res.errors)
#                 return display_response(
#                     msg="FAIL",
#                     err=str(location_res.errors),
#                     body={
#                         "log": "Failed at SQUARE api location list"
#                     },
#                     statuscode=status.HTTP_406_NOT_ACCEPTABLE
#                 )
#         except Exception as e:
#             return display_response(
#                 msg="FAIL",
#                 err=str(e),
#                 body={
#                     "log": "Failed at location list try-catch block"
#                 },
#                 statuscode=status.HTTP_406_NOT_ACCEPTABLE
#             )

#         current_date = date.today()
#         formatted_date = current_date.strftime(Ymd)

#         """Step-3 : Create subscription"""
#         try:
#             idem_key = generate_idempotency_key()
#             result = square_client_conn.subscriptions.create_subscription(
#                 body={
#                     "idempotency_key": idem_key,
#                     "location_id": location_id,
#                     "plan_id": plan_id,
#                     "customer_id": customer_id,
#                     "start_date": formatted_date,
#                     "timezone": "Asia/Kolkata"
#                 }
#             )

#             if result.is_success():
#                 print(result.body)
#                 return display_response(
#                     msg="SUCCESS",
#                     err=None,
#                     body={},
#                     statuscode=status.HTTP_200_OK
#                 )
#             elif result.is_error():
#                 print(result.errors)
#                 return display_response(
#                     msg="FAIL",
#                     err=str(result.errors),
#                     body={
#                         "log": "Failed at SQUARE api subscription creation"
#                     },
#                     statuscode=status.HTTP_406_NOT_ACCEPTABLE
#                 )
#         except Exception as e:
#             return display_response(
#                 msg="FAIL",
#                 err=str(e),
#                 body={
#                     "log": "Failed at subscription creation try-catch block"
#                 },
#                 statuscode=status.HTTP_406_NOT_ACCEPTABLE
#             )
