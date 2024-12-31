## Run Project

cd Desktop<br>
mkdir LibMS<br>
git clone https://github.com/sofenter/LibMS.git<br>
cd LibMS<br>
python -m venv lms_env<br>
lms_env\Scripts\activate<br>
pip install -r requirements.txt<br>
REM del db.sqlite3<br>
python manage.py makemigrations lms_app<br>
python manage.py makemigrations<br>
python manage.py migrate<br>
python manage.py runserver<br>

## Push latest commit to vercel
Created admin account and protected SECRET_KEY in settings.py
<br>
Pushed updated repo to vercel as vercel collaborator
