# Blog API Backend Project

    pre-commit run --all-files

**To get started with the Project, follow these simple steps:**

    1. Navigate to the project directory and create a virtual environment by running:
        - python -m venv venv

    2. Activate the virtual environment by running the command:
        - source venv/bin/activate
        OR - .\venv\Scripts\activate

    3. Install the required dependencies by running the command:
        - pip install -r requirements\local.txt
        - pre-commit install

    4. Next, apply the database migrations by running:
        - python manage.py migrate

    5. Create a superuser account by running:
        - python manage.py createsuperuser

    6. Start the Celery worker by running:
        - celery -A config worker -l info

    7. To load data from fixtures, run the command:
        - python load_data.py

    8. Load the static files
        - python manage.py collectstatic

    9. Finally, start the Django server by running:
        - python manage.py runserver


**Note:** If you are using Windows, Windows does not support Celery parallel processing. Therefore, you need to add --pool=solo as a workaround to run the Celery worker in Windows. The command for starting the Celery worker on Windows is:

    - celery -A config worker --pool=solo -l info

**Notes:**
1. Make sure that the Redis server is running.
2. Make sure that you have added .env file in root directory (.env.example format)
3. Make sure that your DB Server is running and listening to port 5432
4. Make sure that you have created the database with same name mentioned in .env file.
5. If you are running this project with docker, make sure that your docker-desktop is running

**More Information**
For more information on the available commands and functionalities of Blog Backend, please refer to the docs/commands.txt file.
