Django Trainee

################################
Running database migrations

- python3 manage.py makemigrations
- python3 manage.py migrate

#################################
Seed data by command

- python3 manage.py loaddata seeder.json

################################
Running the website

- python3 manage.py runserver
  root: 127.0.0.1:8000

###############################
django with mysql

- install mysqlclient==2.03
- create database {name} in settings
- config file my.cnf according to file example.my.cnf

############################
tao i18n

- install gettext
- wrap text
- django-admin makemessages -l {short name language}
- django-admin compilemessages

############################
Run test
python3 manage.py test
python3 manage.py test --verbosity 2 // chi tiet voi 0 1 2 3
python3 manage.py collectstatic// chay khi gap loi ValueError: Missing staticfiles manifest entry...
python3 manage.py test --parallel auto // chay test song song
python3 manage.py test pitch.tests.test_models // test module
python3 manage.py test pitch.tests.test_models.YourTestClass.test_one_plus_one_equals_two

############################
Create file requirements
pip3 freeze > requirements.txt
