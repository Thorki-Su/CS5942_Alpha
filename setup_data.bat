@echo off
echo Step 1: migrate...
python manage.py migrate

echo Step 2: loaddata...
python manage.py loaddata initial_data/customuser.json
python manage.py loaddata initial_data/userprofile.json
python manage.py loaddata initial_data/certificationtype.json
python manage.py loaddata initial_data/conditiontype.json
python manage.py loaddata initial_data/supporttype.json
python manage.py loaddata initial_data/clientprofile.json
python manage.py loaddata initial_data/volunteerprofile.json

echo Done!
pause
