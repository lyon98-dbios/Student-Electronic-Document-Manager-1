#Import Libraries
from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from werkzeug.utils import secure_filename
import os
import random
from flask import make_response
import glob
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import FileField
from flask_wtf.file import FileAllowed, FileRequired
from flask import make_response
import psycopg2
from flask import send_file

app = Flask(__name__, template_folder='templates')
app.secret_key = "secret_key"

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:icecreamK9.@localhost:5432/student_doc'
app.config['FILES'] = 'files' 

db = SQLAlchemy(app)
#Define Student, Admin and OTP Model
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    matric_no = db.Column(db.String(20), nullable=False)
    passkey = db.Column(db.String(30), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(30), nullable=True)

class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class OTP(db.Model):
    __tablename__ = 'otp'
    passkey = db.Column(db.Integer, primary_key=True)
    matric_no =db.Column(db.String(30), nullable=False)



#Define Document Model
ALLOWED_EXTENSIONS = ['pdf', 'doc', 'docx', 'txt', 'pptx', 'jpeg', 'png', 'jpg']

class DocumentForm(FlaskForm):
    file = FileField('File', validators=[FileRequired(), FileAllowed(ALLOWED_EXTENSIONS, 'Only DOCX, TXT, PPTX, JPG, PNG, JPEG, DOC, and PDF files allowed.')])

'''class DocumentForm(FlaskForm):
    file = FileField('File', validators=[FileAllowed(ALLOWED_EXTENSIONS, 'Only DOCX, TXT, PPTX, JPG, PNG, JPEG, DOC and PDF files allowed.')])'''
class Doc(db.Model):
    __tablename__ = 'docs'
    id = db.Column(db.Integer, primary_key=True)
    file = db.Column(db.String(255), nullable=False) #check
    filename = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    access_type = db.Column(db.String(50), nullable=False)

conn = psycopg2.connect(
       host='localhost',
       port='5432',
       database='student_doc',
       user='postgres',
       password='icecreamK9.')

cursor = conn.cursor()


# Upload Document
@app.route('/upload_document', methods=['GET', 'POST'])
def upload_document():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['FILES'], filename)
            file.save(file_path)

            # Create Doc Instance
            new_doc = Doc(file=file_path, filename=request.form['filename'], description=request.form['description'], access_type=request.form['access-type'])
            db.session.add(new_doc)
            db.session.commit()

            flash('Document uploaded successfully.')
            # Get the ID of the newly created document
            doc_id = new_doc.id
            return redirect(url_for('user_index', doc_id=doc_id))
        else:
            flash('No file selected.')
            return redirect(url_for('upload_document'))
    else:
        return render_template('upload_document.html')


#Functions
# Check if user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def save_user(first_name, last_name, matric_no, passkey, department, phone_number):
    try:
        with conn.cursor() as cursor:
            query = "INSERT INTO students (first_name, last_name, matric_no, passkey, department, phone_number) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id"
            cursor.execute(query, (first_name, last_name, matric_no, passkey, department, phone_number))
            user_id = cursor.fetchone()[0]  # Get the last inserted row ID
            conn.commit()
            return user_id
    except psycopg2.Error as e:
        # Handle the error (e.g., log it or display an error message)
        print("Error saving user:", e)
        return None


#Retrive Docs
def get_uploaded_docs():
    # Retrieve all documents from the database
    docs = Doc.query.all()

    uploaded_docs = []
    for doc in docs:
        uploaded_docs.append(doc.file)

    return uploaded_docs

#Retrive doc by doc id
def retrieve_document(doc_id):
    doc = Doc.query.filter_by(file=doc_id).first()
    if doc:
        return doc
    else:
        return None

# Retrieve file from doc
def get_uploaded_file(doc_id):
    doc = Doc.query.get(doc_id)
    if doc:
        return doc.file
    else:
        return None

#Retrive doc by doc id
def retrieve_document_id(doc_id):
    doc = Doc.query.filter_by(file=doc_id).first()
    if doc:
        return doc.id
    else:
        return None

#Database Queries
def query_db(matric_no):
    cursor = conn.cursor()
    query = "SELECT passkey FROM Students WHERE matric_no = %s"
    cursor.execute(query, (matric_no,))
    result = cursor.fetchone()
    cursor.close()

    if result:
        return result[0]
    else:
        return None

def query_db_otp(passkey):
    cursor = conn.cursor()
    query = "SELECT passkey FROM otp WHERE passkey = %s"  # Specify the column name in the WHERE clause
    cursor.execute(query, (passkey,))
    result = cursor.fetchone()
    cursor.close()

    if result:
        return result[0]
    else:
        return None



#VIEW Functions
@app.route('/')
@login_required
def admin_index(): # Replace with your implementationplate('admin_index.html')
   return render_template('admin_index.html')

@app.route('/user_index')
@login_required
def user_index():
    # Retrieve the documents from the database
    documents = Doc.query.all()

    # Pass the documents to the template context
    return render_template('user_index.html', documents=documents)






@app.route('/profile')
@login_required
def profile():
    matric_no = session['username']
    cursor = conn.cursor()
    query = "SELECT * FROM Students WHERE matric_no = %s"
    cursor.execute(query, (matric_no,))
    user = cursor.fetchone()
    cursor.close()

    if user:
        return render_template('profile.html', user=user)
    else:
        flash('User not found.')
        return redirect(url_for('admin_index'))


@app.route('/edit_document/<doc_id>', methods=['GET', 'POST'])
@login_required
def edit_document(doc_id):
    cursor = conn.cursor()
    if request.method == 'POST':
        #doc = retrieve_document(doc_id=doc_id)
        # Retrieve the edited document details from the form
        filename = request.form['filename']
        access = request.form['access']

        # Update the document in the database
        query = "UPDATE Documents SET title = %s, access = %s WHERE id = %s"
        values = (filename, access, doc_id)
        cursor.execute(query, values)
        conn.commit()
        return redirect(url_for('edit_document', doc_id=doc_id))
        
    else:
        # Retrieve the document details from the database
        query = "SELECT * FROM Documents WHERE id = %s"
        cursor.execute(query, (doc_id,))
        document = cursor.fetchone()
        cursor.close()
        
        return render_template('edit_document.html', doc_id=doc_id)

# User management
@app.route("/user_management")
def user_management():
    # Fetch all user data from the database
    cursor = conn.cursor()
    query = "SELECT * FROM Students"
    cursor.execute(query)
    users = cursor.fetchall()
    cursor.close()
    return render_template('user_management.html', Users=users)


# Add user
@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        session['matric_number'] = request.form['matric-number']
        return redirect(url_for('generate_otp'))
    else:
        return render_template('add_user.html')
    


@app.route('/generate_otp', methods=['POST'])
@login_required
def generate_otp():
    matric_number = request.form.get('matric-number')
    
    if matric_number:
        otp = random.randint(100000, 999999)
        
        # Store the OTP and matric number in the database
        # (Make sure to have a table named 'otp' with 'passkey' and 'matric_no' columns)
        cursor =conn.cursor()
        query = "INSERT INTO otp (matric_no, passkey) VALUES (%s, %s)"
        cursor.execute(query, (matric_number, otp))
        conn.commit()
        cursor.close()
        
        flash('User added successfully')
        return render_template('generate_otp.html', otp=otp, matric_number=matric_number)
    else:
        flash('Matric number not found')
        return redirect(url_for('add_user'))
    
# Route for the Edit User page
@app.route('/edit_user', methods=['GET', 'POST'])
def edit_user():
    if request.method == 'POST':
        user_id = request.form['user_id']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        department = request.form['department']
        phone_number = request.form['phone_number']
        
        # Update the user's details in the database
        cursor = conn.cursor()
        query = "UPDATE Students SET first_name = %s, last_name = %s, department = %s, phone_number = %s WHERE id = %s"
        cursor.execute(query, (first_name, last_name, department, phone_number, user_id))
        cursor.commit()
        cursor.close()
        
        flash('User details updated successfully')
        return redirect(url_for('edit_user'))
    else:
        # Retrieve all users from the database
        cursor = conn.cursor()
        query = "SELECT * FROM Students"
        cursor.execute(query)
        users = cursor.fetchall()
        cursor.close()
        
        return render_template('edit_user.html', users=users)
# Route for the Delete User page
@app.route('/delete_user', methods=['GET', 'POST'])
def delete_user():
    if request.method == 'POST':
        if 'delete_selected' in request.form:
            selected_users = request.form.getlist('selected_users')
            
            # Delete the selected users from the database
            cursor = conn.cursor()
            for user_id in selected_users:
                query = "DELETE FROM Students WHERE id = %s"
                cursor.execute(query, (user_id,))
            conn.commit()
            cursor.close()
            
            flash('Selected users deleted successfully')
        elif 'delete_all' in request.form:
            # Delete all users from the database
            cursor = conn.cursor()
            query = "DELETE FROM Students"
            cursor.execute(query)
            conn.commit()
            cursor.close()
            
            flash('All users deleted successfully')
        
        return redirect(url_for('delete_user'))
    else:
        # Retrieve all users from the database
        cursor = conn.cursor()
        query = "SELECT * FROM Students"
        cursor.execute(query)
        users = cursor.fetchall()
        cursor.close()
        
        return render_template('delete_user.html', users=users)



# Login page
@app.route('/login', methods=['GET', 'POST'])
def login(

):
    if request.method == 'POST':
        if 'otp' in request.form:
            # Handle OTP submission
            otp = request.form['otp']
            # Process OTP here
            stored_otp = query_db_otp(otp)
            if stored_otp is not None:
                return redirect(url_for('register'))
            else:
                flash('Invalid OTP')
        else:
            # Handle username and password submission
            matric_no = request.form['username']
            passkey = request.form['password']
            stored_password = query_db(matric_no)
            # Process username and password here
            if matric_no == 'admin' and passkey == 'admin':
                session['username'] = matric_no
                return redirect(url_for('admin_index'))
            elif stored_password is not None and stored_password == passkey:
                session['username'] = matric_no
                return redirect(url_for('user_index'))
            else:
                flash('Invalid username or password')
    # Display login form
    return render_template('login.html')


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form["first-name"]
        last_name = request.form["last-name"]
        matric_no = request.form["matric-no"]
        passkey = request.form["password"]
        confirm_password = request.form["confirm-password"]
        department = request.form["department"]
        phone_number = request.form["phone-number"]
        
        if passkey != confirm_password:
            flash("Passwords do not match.")
        else:
            user_id = save_user(first_name, last_name, matric_no, passkey, department, phone_number)
            if user_id is not None:
                session['matric_no'] = matric_no
                flash("Registration successful.")
                return redirect(url_for('login'))
            else:
                flash("An error occurred during registration.")
    
    return render_template('registeration_user.html')


@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    session.pop('logged_in', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))


from flask import send_file

from flask import send_from_directory

@app.route('/download_document/<doc_id>')
def download_document(doc_id):
    document = retrieve_document(doc_id)
    if document:
        return render_template('download_document.html', document=document)
    else:
        flash('Document not found.', 'error')
        return redirect(url_for('user_index'))
    
@app.route('/download/<doc_id>')
def download(doc_id):
    document = Doc.query.get(doc_id)
    if document:
        file_path = os.path.join(app.config['FILES'], document.filename)
        return send_from_directory(app.config['FILES'], file_path, as_attachment=True)
    else:
        flash('Document not found.', 'error')
        return redirect(url_for('user_index'))
    
    
# Delete Document
@app.route('/delete_document/<doc_id>', methods=['GET', 'POST'])
@login_required
def delete_document(doc_id):
    cursor = conn.cursor()
    if request.method == 'POST':
        # Retrieve the document details from the database
        query = "SELECT * FROM Documents WHERE id = %s"
        cursor.execute(query, (doc_id,))
        document = cursor.fetchone()

        if document:
            # Delete the document from the database
            query = "DELETE FROM Documents WHERE id = %s"
            cursor.execute(query, (doc_id,))
            conn.commit()

            # Delete the document file from the server
            file_path = document['file_path']
            if os.path.exists(file_path):
                os.remove(file_path)

            flash('Document deleted successfully.')
            return redirect(url_for('user_index'))
        else:
            flash('Document not found.')
            return redirect(url_for('user_index'))
        
    else:
        # Retrieve the document details from the database
        query = "SELECT * FROM Documents WHERE id = %s"
        cursor.execute(query, (doc_id,))
        document = cursor.fetchone()
        cursor.close()

        if document:
            return render_template('delete_document.html', doc_id=doc_id)
        else:
            flash('Document not found.')
            return redirect(url_for('user_index'))

if __name__ == '__main__':
    app.run(debug=True)

