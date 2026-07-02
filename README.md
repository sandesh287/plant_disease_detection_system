# Plant Disease Detection System

This is a Django web application for detecting plant diseases from uploaded leaf images. It uses:

- Django for the web application
- MongoDB Atlas for users, plant facts, disease details, and profile data
- TensorFlow/Keras CNN model for image feature extraction
- Random Forest model for final disease classification

The Django project is inside the `MyProject` folder.

## Important Notes

This project does need MongoDB. It does not use the included `db.sqlite3` for the main app data. User signup/login, plant information, disease information, and profile data are handled through MongoDB Atlas.

The current pinned machine learning dependencies are old enough that Python 3.14 is not recommended. Use Python 3.10 if possible.

## Prerequisites

Install these before running the project:

1. Python 3.10
2. Git
3. MongoDB Atlas account
4. Code editor or terminal

Check your Python version:

```powershell
python --version
```

If this shows Python 3.14, install Python 3.10 and use the Python launcher commands shown below.

## MongoDB Atlas Setup

1. Open MongoDB Atlas.
2. Create a project and cluster if you do not already have one.
3. Create a database user.
4. Allow your IP address in Network Access.
   - For local testing, you can temporarily allow `0.0.0.0/0`.
   - For real use, restrict this to your actual IP.
5. This project expects the database name:

```text
Project_Database
```

6. The app will automatically create and populate these collections when it starts:

```text
disease_data
plant_info
user
profile_details
```

The MongoDB cluster host is currently hard-coded in `MyProject/myapp/db.py`:

```text
project-1.ourfx.mongodb.net
```

If your Atlas cluster has a different host, update that value in `MyProject/myapp/db.py`.

## Environment Variables

Create a `.env` file inside the `MyProject` folder:

```powershell
cd MyProject
New-Item .env
```

Add your MongoDB Atlas username and password:

```env
MONGO_USERNAME=your_mongodb_username
MONGO_PASSWORD=your_mongodb_password
```

Do not commit `.env` to GitHub.

## Setup on Windows PowerShell

From the project root:

```powershell
cd E:\practice_projects\Plant-Disease-Detection-System\MyProject
```

Create a virtual environment with Python 3.10:

```powershell
py -3.10 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

If TensorFlow installation fails, first confirm that your virtual environment is using Python 3.10:

```powershell
python --version
```

## Run Database Checks

The app uses MongoDB directly, but Django can still run its standard checks:

```powershell
python manage.py check
```

If this fails with `Username and password must be strings`, your `.env` file is missing or is not inside the `MyProject` folder.

If this fails with a MongoDB connection error, check:

- Atlas username/password
- Atlas Network Access IP allowlist
- Cluster host in `myapp/db.py`
- Internet connection

## Create Admin User

This project includes a command that creates a default admin user in MongoDB:

```powershell
python manage.py create_admin
```

Default credentials:

```text
Email: admin@gmail.com
Password: admin
```

Change this password before using the app seriously.

## Run the App

Start the Django development server:

```powershell
python manage.py runserver
```

Open the app in your browser:

```text
http://127.0.0.1:8000/
```

Useful pages:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/signup/
http://127.0.0.1:8000/login/
http://127.0.0.1:8000/test/
http://127.0.0.1:8000/profile/
```

## How to Test the Detection Flow

1. Run the server.
2. Open `/test/`.
3. Upload a `.jpg`, `.jpeg`, or `.png` leaf image.
4. Click the detect button.
5. Without login, the app shows partial disease information.
6. After signup/login, the app shows full disease information.

Sample uploaded images already exist in:

```text
MyProject/media/uploads/
```

## Model Files

The detection code expects these files:

```text
MyProject/myapp/models/fix_model.h5
MyProject/myapp/models/rf_fix_model.pkl
```

If either file is missing, prediction will fail.

## Common Problems

### `ModuleNotFoundError: No module named 'django'`

Your virtual environment is not activated or dependencies are not installed.

Fix:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### `Username and password must be strings`

The app cannot read MongoDB credentials.

Fix:

- Create `.env` inside `MyProject`
- Add `MONGO_USERNAME` and `MONGO_PASSWORD`
- Restart the terminal/server

### TensorFlow install fails

Use Python 3.10. The pinned TensorFlow version in `requirements.txt` is not suitable for the newest Python versions.

### MongoDB authentication fails

Check that:

- Username is correct
- Password is correct
- Special characters in the password are okay
- Your IP is allowed in Atlas Network Access
- The cluster host in `myapp/db.py` matches your Atlas cluster

### App starts slowly

This is expected. At startup it loads TensorFlow models and connects to MongoDB.

## Project Structure

```text
Plant-Disease-Detection-System/
|-- README.md
|-- phase2CNNmodel.ipynb
`-- MyProject/
    |-- manage.py
    |-- requirements.txt
    |-- .env
    |-- MyProject/
    |   |-- settings.py
    |   `-- urls.py
    |-- myapp/
    |   |-- db.py
    |   |-- views.py
    |   |-- predict.py
    |   |-- middleware.py
    |   |-- models/
    |   |   |-- fix_model.h5
    |   |   `-- rf_fix_model.pkl
    |   `-- management/commands/create_admin.py
    |-- template/
    |-- static/
    `-- media/
```

## Team Members

- Ashmita Timalsina - https://github.com/Ashmita1555
- Ruth Ghising - https://github.com/RuthTmg
- Anjal Ghimire
