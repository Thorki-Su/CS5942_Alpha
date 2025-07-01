@echo off
python manage.py dumpdata user.CustomUser --indent 2 > initial_data/customuser.json
python manage.py dumpdata user.UserProfile --indent 2 > initial_data/userprofile.json
python manage.py dumpdata user.CertificationType --indent 2 > initial_data/certificationtype.json
python manage.py dumpdata user.ConditionType --indent 2 > initial_data/conditiontype.json
python manage.py dumpdata user.SupportType --indent 2 > initial_data/supporttype.json
python manage.py dumpdata user.ClientProfile --indent 2 > initial_data/clientprofile.json
python manage.py dumpdata user.VolunteerProfile --indent 2 > initial_data/volunteerprofile.json
pause
