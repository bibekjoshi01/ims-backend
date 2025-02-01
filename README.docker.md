**Docker Commands**
docker-compose up --build
docker-compose stop
docker-compose down / docker-compose down -v

**Executing Commands**
docker-compose exec ims-backend-web-1 python manage.py migrate
docker-compose exec ims-backend-web-1 python manage.py createsuperuser
docker-compose exec ims-backend-web-1 python loaddata.py
