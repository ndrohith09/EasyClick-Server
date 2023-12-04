from django.db import models

'''----------Start : User Model----------'''
class User(models.Model):
    """Personal details"""
    merchant_id = models.CharField(max_length=256,unique=True,null=True,blank=True)
    active = models.BooleanField(default=True)
    """Company details"""
    company_name = models.CharField(max_length=256,null=True,blank=True)
    company_country = models.CharField(max_length=256,null=True,blank=True)
    company_currency = models.CharField(max_length=256,null=True,blank=True) #----above is square response models fields
    company_phone = models.CharField(max_length=256,null=True,blank=True)
    company_email = models.CharField(max_length=256,null=True,blank=True)
    company_website = models.CharField(max_length=256,null=True,blank=True)
    company_logo = models.CharField(max_length=256,null=True,blank=True)
    """Social details"""
    facebook = models.CharField(max_length=256,null=True,blank=True)
    twitter = models.CharField(max_length=256,null=True,blank=True) 
    linkedin = models.CharField(max_length=256,null=True,blank=True)
    instagram = models.CharField(max_length=256,null=True,blank=True)
    """Other details"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    """Live thirdparty api access token"""
    access_token = models.CharField(max_length=512,null=True,blank=True)
    refresh_token = models.CharField(max_length=512,null=True,blank=True)
    expires_at = models.CharField(max_length=512,null=True,blank=True)

    def __str__(self):
        return str(self.company_name)


'''----------Start : Subscription Model----------'''
"""
    Industry id:
        - Health and Fitness: 1
        - Food and Beverage: 2
"""
class SubscriptionModel(models.Model):
    merchant_id = models.CharField(max_length=256,null=True, blank=True)

    """Analytics key"""
    analytics_key = models.CharField(max_length=256 , null=True , blank=True)

    """Industry details"""
    industry_id = models.CharField(max_length=256,null=True, blank=True)
    industry = models.CharField(max_length=512,null=True, blank=True)  
    """Group details"""
    group = models.CharField(max_length=512,null=True, blank=True)
    group_enabled = models.BooleanField(default=True)
    """Plan details"""
    plan = models.JSONField(default=list,null=True, blank=True)
    disabled_plans = models.JSONField(default=list,null=True, blank=True)
    """Share details"""
    endpoint_path = models.CharField(max_length=512,null=True, blank=True,unique=True)
    api_endpoints = models.CharField(max_length=512,null=True, blank=True)
    template_type = models.CharField(max_length=256,null=True,blank=True)
    """Subscribed people"""
    subscribed_people = models.JSONField(default=list,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 
    def __str__(self):
        return str(self.industry)

'''----------Start : Plan Model----------'''
class PlanModel(models.Model):
    plan_id = models.CharField(max_length=256,null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    points = models.JSONField(default=list,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.plan_id)

class SquareSubModel(models.Model):
    """Payment model"""
    pay_amt = models.CharField(max_length=512,null=True,blank=True)
    card_holder_name = models.CharField(max_length=512,null=True,blank=True)
    email = models.CharField(max_length=512,null=True,blank=True)
    mobile = models.CharField(max_length=512,null=True,blank=True)
    card_number = models.CharField(max_length=256,null=True,blank=True)
    card_expiry = models.CharField(max_length=256,null=True,blank=True)
    industry = models.CharField(max_length=256,null=True,blank=True )
    company_name = models.CharField(max_length=256,null=True,blank=True )
    plan = models.CharField(max_length=256,null=True,blank=True )
    databricks_updated=models.BooleanField(default=False)


''''
CRM Fields 
Name : card_holder_name
Primary Address : 

'''