## EasyClick 

EasyClick is a subscription management platform that uses predictive analytics for customer loyalty ratings, enabling businesses to target key customer segments. It not only simplifies subscription management but also transforms it into a strategic asset for businesses, driving growth and fostering long-lasting customer relationships.

---
## How we built it

Here's an overview look at the key components and strategies we employed:

#### Backend Development and API Integration
- **Robust Backend with Django**: The backend is built with the Django framework which supports complex subscription management tasks.
- **Django REST Framework for API Services**: We utilized Django REST Framework for creating RESTful APIs to make data transfer and retrieval.

![arch](https://github.com/ndrohith09/EasyClick-Client/assets/75234968/241fa5b7-e266-446d-a468-cab250758c33)

#### Task Scheduling and Data Management
- **Celery for Background Task Management**: We integrated Celery, a distributed task queue,to facilitate scheduled runs for pushing data from our local database to the Databricks data warehouse. 
- **Redis as a Message Broker**: Redis plays a pivotal role in our architecture, acting as a message broker between Django and Celery. It ensures efficient handling of task queues and real-time data processing.

#### Data Storage and Processing
- **Databricks Data Warehouse**: For robust data storage and advanced processing, we chose Databricks as our data warehousing solution. It stores vast amounts of customer data and feeds into our machine learning pipeline for analyzing customer loyalty.

![data_analysis](https://github.com/ndrohith09/EasyClick-Client/assets/75234968/7c761a94-1882-47a9-aa74-9f65bd8c355a)

- **Machine Learning for Predictive Analytics**: Our journey in predictive modeling involved exploring various machine learning algorithms. After the model comparison, we found Residual networks to deliver the highest classification accuracy for predicting customer loyalty ratings.

![model](https://github.com/ndrohith09/EasyClick-Client/assets/75234968/925797c6-d459-40d5-b949-e4bb450914d9)

#### Integration with Third-Party Services
- **Twilio SendGrid for Email Marketing**: To enhance our marketing efforts, we integrated Twilio SendGrid. This powerful tool enables us to send personalized email campaigns based on customer loyalty scores, directly impacting customer engagement and retention.
- **Close CRM for Management**: Close CRM was chosen for its robustness in managing customer relationships. It helps us keep track of customer interactions, subscriptions, and feedback, all in one place.
- **Square's Payment API for Payments**: For secure and reliable payment processing, we integrated Square's Payment API. It simplifies the transaction process, offering a safe and convenient payment experience for our users.
- **AWS S3 for Data Analytics**: We leveraged Amazon S3 for its unparalleled data analytics capabilities. It serves as a repository for storing and analyzing large-scale customer data, providing us with actionable insights.

![twilio segment](https://github.com/ndrohith09/EasyClick-Client/assets/73429989/625d06ba-af59-4409-af81-3d8b0d8068c0)

---

### EasyClick Server 

Clone this [server repo](https://github.com/ndrohith09/EasyClick-Server) and run the following commands 
````bash
git clone https://github.com/ndrohith09/EasyClick-Server.git
cd Square-Server
````
Change the secrets in the [settings.py](https://github.com/ndrohith09/EasyClick-Server/blob/main/squarebackend/settings.py) file
```python 
BASE_URL =  "http://localhost:8000" # your server url
SQUARE_APP_ID= "sandbox-****-***" # your square app id
SQUARE_APP_SECRET = "***" # your square app secret
SQUARE_API_URL = "https://connect.squareupsandbox.com"
SQUARE_SANDBOX_TOKEN = "*****" # your square sandbox token

```

To run the server you need to install the requirements and run the following command
```bash
pip install -r requirements.txt
python3 manage.py runserver 0.0.0.0:8000
```

<hr />
<br />

### EasyClick Client

Clone this [client repo](https://github.com/ndrohith09/EasyClick-Client) and run the following commands 

````bash
git clone https://github.com/ndrohith09/EasyClick-Client.git
cd EasyClick-Client
````

Install the dependencies and run the following command
```bash
yarn install
 (or)
npm install
```

Change the api **baseURL** according to your server url in the [api.jsx](https://github.com/ndrohith09/EasyClick-Client/blob/master/src/api/api.jsx) file
```javascript  
 baseURL : 'https://0.0.0.0:8000/api/v1/',
```
Start the client
```bash 
yarn dev
 (or)
npm run dev
```

# Celery-Instructions

Install redis in host machine

#### Package installation

``` pip install -r requirements.txt```

#### Starting the worker
```celery -A squarebackend.celery worker --pool=solo -l info```

#### starting periodic worker
```celery -A squarebackend beat -l INFO```