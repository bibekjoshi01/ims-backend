# Blog Backend Project

**Formatting and Linting Code**

1. ruff check / ruff check --fix / ruff format
2. black .
3. pre-commit run --all-files

**To get started with the Project, follow these simple steps:**

    1. Navigate to the project directory and create a virtual environment by running:
        - python -m venv venv

    2. Activate the virtual environment by running the command:
        - source venv/bin/activate
        OR - .\venv\Scripts\activate

    3. Install the required dependencies by running the command:
        - pip install -r requirements\base.txt
        - pre-commit install

    4. Next, apply the database migrations by running:
        - python manage.py migrate

    5. Create a superuser account by running:
        - python manage.py createsuperuser

    6. Start the Celery worker, beat and flower by running:
        - celery -A config worker -l info
        - celery -A config flower
        - celery -A config beat --loglevel=info

    7. To load data from fixtures, run the command:
        - python loaddata.py

    8. Load the static files
        - python manage.py collectstatic

    9. Finally, start the Django server by running:
        - python manage.py runserver

 - Configure third party creds (for Paypal, Stripe, Google etc)
 - Configure Email creds (for verification mails etc.)


**Note:** If you are using Windows, Windows does not support Celery parallel processing. Therefore, you need to add --pool=solo as a workaround to run the Celery worker in Windows. The command for starting the Celery worker on Windows is:

    - celery -A config worker --pool=solo -l info
    - celery -A config flower
    - celery -A config beat --loglevel=info -l info


**For Text Translation**
    Download:
        Windows: https://mlocati.github.io/articles/gettext-iconv-windows.html
        Linux: sudo apt-get install gettext

    django-admin makemessages -l np --ignore=venv/*  # For Nepali
    django-admin makemessages -l en --ignore=venv/* # For English (if needed)
    django-admin compilemessages --ignore=venv/*
