# Shallion Support: Client - Volunteer Matching System 
CS5942: MSC PROJECT IN INFORMATION TECHNOLOGY  
Team Alpha


## 1. Introduction
This system is designed to help Shallion Support manage the task allocation, communication and donation processes between volunteers and customers more efficiently, and ensure information security and user experience.


## 2. Tech Stack
Backend: Django  
Frontend: HTML, CSS, JavaScript  
Database: PostgreSQL, SQLite  
Cloud Services: AWS S3, SendGrid, Stripe  


## 3. Features
User registration and login (User selectable roles)  
User email authentication  
Task posting and undertaking
Real-time text, voice and video calls  
Donation System  
Upload files and pictures  
User information review  


## 4. Getting Started
### 1) Cloning this project

You can clone the project from our Github repository:
```bash
git clone https://github.com/Thorki-Su/CS5942_Alpha.git
cd CS5942_Alpha
```

### 2) Create a virtual environment and install dependencies
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 3) Copy the environment variable template

The project file contains the *.env.example* file, which serves as a template for environment variables. The following command will copy it and name it *.env*.
```bash
cp .env.example .env
```

### 4) Configure the .env file (for details, see Environment Variables)
### 5) Run the migration and start the project
```bash
python manage.py migrate
python manage.py runserver
```


## 5. Environment Variables
In *.env* file, we store the API keys for tools we use, such as AWS, postsql, SendGrid and Stripe. Getting a new key is necessary if you want to run the local version. 

Please note:
1. You need to register an account on the respective service platform, create a project or application, and get the corresponding keys.

2. Fill these keys into the local *.env* file to ensure that the project can call the relevant APIs properly.

3. Do not submit the *.env* file containing the real keys to the public codebase. This could trigger a serious security alert.

4. Please refer to the *.env.example* file for the specific key name and follow the instructions to get it from the corresponding platform.


## 6. Branch Protection Policy
To ensure the stability of the code base, we have implemented strict protection policies for the main branch:
1. Direct Push to the main branch is prohibited. All modifications must be made through Pull Request (PR).
2. PR can only be merged after being reviewed and approved by at least one team member other than the initiator to ensure code quality and security.
3. Make sure to merge only after passing the automated test (CI/CD) to prevent error code from entering the main branch.
4. Prohibit force push or deletion of the main branch to avoid data loss.

This strategy helps us prevent unreviewed code from directly affecting the production environment and ensures that each launch is fully verified. Subsequently, the development team can refer to and adjust this protection strategy based on the actual situation to ensure the standardization and security of code management.


## 7. Testing
Run unit tests:
```bash
python manage.py test
```

### Multi-User Concurrent Testing (20-100 Users)


### 1) Install Dependencies
```bash
pip install locust
```

### 2) Start Django Server
```bash
python manage.py runserver
```

### 3) Run Test

```bash
python run_multi_user_test.py
```

### Recommended Settings
- **Number of Users**: 20-100
- **Spawn Rate**: 5-10 users/second
- **Test Duration**: 5-10 minutes



## 8. Deployment
We used the Render platform for deployment. You can visit the deploy version through https://cs5942-alpha.onrender.com/  
We have applied for a dedicated account for this project:
| Username              | Password                 |
|---------------------|----------------------|
|    shallion9527@gmail.com       | Shallionsupport9527!         |


## 9. Accounts
During the development and testing process, we created some accounts:
| Username              | Password                 | Role                  |
|---------------------|----------------------|-------------------------|
| shallion9527@gmail.com          | Shallionsupport9527!          | admin    |
| Applejuice@gmail.com          | Test123456          | client    |
| Bananamilk@gmail.com          | Test123456          | volunteer    |


