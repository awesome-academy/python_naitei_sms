Django Trainee

################################
Running database migrations

- python manage.py makemigrations
- python manage.py migrate

#################################
Seed data by command

- python manage.py loaddata pitch_and_images_data.json
- create fulltext search
- run command in mysql
  ALTER TABLE pitches
  ADD FULLTEXT(title, description);

################################
Running the website

- python manage.py runserver
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

- Tạo file staticfiles nếu không có //python3 manage.py collectstatic
  python3 manage.py test
  python3 manage.py test --verbosity 2 // chi tiet voi 0 1 2 3
  python3 manage.py collectstatic// chay khi gap loi ValueError: Missing staticfiles manifest entry...
  python3 manage.py test --parallel auto // chay test song song
  python3 manage.py test pitch.tests.test_models // test module
  python3 manage.py test pitch.tests.test_models.YourTestClass.test_one_plus_one_equals_two

############################
Use Venv
Run command creaet virtual environment
python -m venv env
Create file requirements
pip3 freeze > requirements.txt
source env/bin/activate
Install Package
pip install -r requirements.txt

############################
schedule job
python manage.py crontab add
python manage.py crontab show
python manage.py crontab remove
