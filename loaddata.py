# ruff: noqa
import os

os.system("python manage.py loaddata main_module")
os.system("python manage.py loaddata permission_category")
os.system("python manage.py loaddata permissions")
os.system("python manage.py loaddata user_role")
