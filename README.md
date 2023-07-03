# Student-Electronic-Document-Manager
 Student Electronic Document Manager for Lead City University
pip install -r requirements.txt
pip install flask-migrate

flask db initgrate -m "Initial migration"
flask db upgrade



