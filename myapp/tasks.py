from .models import *
from celery import shared_task

from databricks import sql

import os



@shared_task(bind=True)
def update_db(self):
    print("Done")
    #operations
    connection = sql.connect(
                        server_hostname = "dbc-0d552672-a5bb.cloud.databricks.com",
                        http_path = "/sql/1.0/warehouses/5c423c56fa723fbd",
                        access_token = "dapi9ee739fa2784747514a23c4c5101089f")
                        # access_token = "<access-token>")

    cursor = connection.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS SquareSubModel (pay_amt varchar(20), card_holder_name varchar(20),email varchar(20),mobile varchar(20),card_number varchar(20), card_expiry varchar(20),industry varchar(20),company_name varchar(20),plan varchar(20))")
    
    square_query_set=SquareSubModel.objects.filter(databricks_updated=False)
    for s_i in square_query_set:

        values=f"('{s_i.pay_amt}','{s_i.card_holder_name}','{s_i.email}','{s_i.mobile}','{s_i.card_number}','{s_i.card_expiry}','{s_i.industry}','{s_i.company_name}','{s_i.plan}')"
        cursor.execute(f"INSERT INTO SquareSubModel (pay_amt,card_holder_name,email,mobile,card_number,card_expiry,industry,company_name,plan) VALUES {values}")
        s_i.databricks_updated=True
        s_i.save()
    cursor.close()
    connection.close()
    
    return "Done"