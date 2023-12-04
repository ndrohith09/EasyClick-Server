from django.urls import path
from .views import *
urlpatterns=[
    #-----Square oauth----
    path('oauth-authorize/',OAuthAuthorize.as_view(),name="oauth-authorize"), #make the client authorize and returns oauth permissions url
    path('oauth-callback/',OAuthRedirect.as_view(),name="oauth-callback"), #make the client callback and returns oauth token
    
    #-----Square api----
    path('create-group/',NewGroupIndustry.as_view(),name="create-group"), #create a new group in a industry (only in our db)
    path('create-plan/',NewSubscriptionPlan.as_view(),name="create-plan"), #create a new subscription plan in both our db and square
    path('make-payment/',MakePayment.as_view(),name="make-payment"), #select a plan and makepayment,after payment confirmatin, subscription is made

    path('get-people/',GetSubscriptions.as_view(),name="get-people"), #get the list of people subscribed to plans
    path('view-plans/',GetAllGroups.as_view(),name="view-plans"), #get the list of plans in a group
    path('update-group/',UpdateGroup.as_view(),name="update-group"), #update the group name
    path('status-plan/',EnableDisablePlan.as_view(),name="update-plan"), #update the plan status
    path('edit-plan/',EditPlan.as_view(),name="edit-plan"), #update the plan details
    path('profile/',ProfileSettings.as_view(),name="profile"), #update the profile details
    path('dashboard/',DashboardAnalytics.as_view(),name="dashboard"), #get the dashboard details
    path('all-invoices/',AllInvoice.as_view(),name="all-invoices"), #get the list of all invoices

    #----Not used----
    # path('login/',LoginUser.as_view(),name="login-user"),
    # path('register/',RegisterAPI.as_view(),name="register"),
    # path('subscribe-plan',SubscribeToPlan.as_view(),name="subscribe-plan"),
    path('test/',TestResponse.as_view(),name="test-response")

]