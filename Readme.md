# Celery-Instructions

Install redis in host machine

#### Package installation

``` pip install -r requirements.txt```

#### Starting the worker
```celery -A squarebackend.celery worker --pool=solo -l info```

#### starting periodic worker
```celery -A squarebackend beat -l INFO```