# CS5942: MSC PROJECT IN INFORMATION TECHNOLOGY
# Team Alpha
In this file we will introduce each parts in the project.

# How to run

# Project Structure
Our project's name is '**final_project**'.  
There are **7** apps in the project. They are **adminpanel**, **communication**, **matching**, **payment**, **task**, **user** and **volunteer**.  
We use env file to store some keys. You can see the load method in settings.py.  

## user
This app is about users' registeration and logging-in.

### models.py
**CustomUserManager**: Since we plan not to use usernames, but rather email addresses for logins, we use this to make changes to the default user model.

**CustomUser**: Changed user model with email, password and user type.

**user_directory_path**: The function used to generate the file storage path.

**UserProfile**: Used to store information that is shared between different types of user.

**CertificationType**: Used to store the certification types.

**ConditionType**: Used to store the condition types.

**SupportType**: Used to store the support types.

**ClientProfile**: Used to store information unique to the client.

**VolunteerProfile**: Used to store information unique to the volunteer.

**AdminProfile**: Used to store information unique to the admin.

### forms.py
**ClientRegisterForm**, **VolunteerRegisterForm**: Two register forms.

**ClientProfileForm**, **VolunteerProfileForm**: Two forms used to change profile information.

**ProfilePhotoForm**: The form used to change profile photo.

### utils.py
**normalize_uk_postcode**: Normalize the user input postcode.

**is_valid_aberdeen_postcode**: Check the user input postcode is in Aberdeen or not.

**geocode_address**: Use the user input postcode to get the coordinate.

**send_activation_email**: To send a check email to user.

## task

## communication

## matching

## adminpanel

## volunteer

## payment