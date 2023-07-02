from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from werkzeug.utils import secure_filename
import threading
import os
import mysql.connector
from flask_mysqldb import MySQL
import random
import uuid
from werkzeug.routing import UUIDConverter
from flask.helpers import send_file
from flask import make_response
import glob
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import FileField
from wtforms.validators import FileAllowed
from flask import make_response

app = Flask(__name__, template_folder='templates')
app.secret_key = "secret_key"

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:icecreamK9.@localhost:5432/student_doc'
db = MySQL(app)

#Define Document Model

ALLOWED_EXTENSIONS = ['pdf', 'doc', 'docx', 'txt', 'pptx', 'jpeg', 'png', 'jpg']
class DocumentForm(FlaskForm):
    file = FileField('File', validators=[FileAllowed(ALLOWED_EXTENSIONS, 'Only DOCX, TXT, PPTX, JPG, PNG, JPEG, DOC and PDF files allowed.')])

class Doc(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    access_type = db.Column(db.String(50), nullable=False)

#Upload Document
@app.route('/upload_document', methods=['GET', 'POST'])
def upload_doc():
    form = DocumentForm()

    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['FILES'], filename))

        #Create Doc Instance
        new_doc = Doc(file=filename, name=form.name.data, description=form.description.data, access_type=form.access_type.data)
        db.session.add(new_doc)
        db.session.commit()

        #return successful upload
        response = make_response("Document uploaded sucessfully!", 200)
        return response
    else:
        return render_template('upload_document.html', form=form)
    
#Retrive Docs
def get_uploaded_docs():
    # Retrieve all documents from the database
    docs = Doc.query.all()

    uploaded_docs = []
    for doc in docs:
        uploaded_docs.append(doc.file)

    return uploaded_docs

#Get single doc by ID
def get_uploaded_doc_by_id(doc_id):
    # Retrieve the document from the database by its ID
    doc = Doc.query.get(doc_id)

    if doc:
        return doc.file
    else:
        return None

#Retrive doc by file name
def retrieve_document_id(file_name):
    doc = Doc.query.filter_by(file=file_name).first()
    if doc:
        return doc.id
    else:
        return None

def query_db(matric_no):
    cursor = mysql.connection.cursor()
    query = "SELECT passkey FROM Students WHERE matric_no = %s"
    cursor.execute(query, (matric_no,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return result[0]
    else:
        return None


def query_db_otp(otp):
    cursor = mysql.connection.cursor()
    query = "SELECT passkey FROM otp WHERE passkey = %s"  # Specify the column name in the WHERE clause
    cursor.execute(query, (otp,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return result[0]
    else:
        return None


def save_user(first_name, last_name, matric_no, passkey, department, phone_number):
    cursor = mysql.connection.cursor()
    query = "INSERT INTO Students (first_name, last_name, matric_no, passkey, department, phone_number) VALUES (%s, %s, %s, %s, %s, %s)"
    cursor.execute(query, (first_name, last_name, matric_no, passkey, department, phone_number))
    mysql.connection.commit()
    user_id = cursor.lastrowid
    cursor.close()
    return user_id


# Set up file upload folder
app.config['UPLOAD_FOLDER'] = 'uploads'




# Check if a file is an allowed file type
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Check if user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function

document_id = get_document_id()
document = get_document_by_id(document_id) 

# Homepage
@app.route('/')
@login_required
def admin_index():
    document = get_document_by_id(document_id)  # Replace with your implementation
    return render_template('admin_index.html', document=document)
   

@app.route('/user_index')
@login_required
def user_index():
    return render_template('user_index.html')


@app.route('/profile')
@login_required
def profile():
    matric_no = session['username']
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM Students WHERE matric_no = %s"
    cursor.execute(query, (matric_no,))
    user = cursor.fetchone()
    cursor.close()

    if user:
        return render_template('profile.html', user=user)
    else:
        flash('User not found.')
        return redirect(url_for('admin_index'))


@login_required
@app.route('/quick_search',  methods=['GET', 'POST'])
def quick_search():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM documents")
    rows = cursor.fetchall()

    documents = []
    for row in rows:
        document = {
            "id": row[0],
            "title": row[1]
        }
        documents.append(document)

    cursor.close()
    conn.close()

    return render_template('quick_search.html', documents=documents)



@app.route('/search', methods=['POST'])
@login_required
def search():
    keyword = request.form['keyword']
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM Students WHERE first_name LIKE %s OR last_name LIKE %s OR matric_no LIKE %s"
    values = (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%")
    cursor.execute(query, values)
    results = cursor.fetchall()
    cursor.close()

    return render_template('search_results.html', results=results)


@app.route('/documents/<document_id>')
def document_route(document_id):
    # Retrieve the document with the given document_id from your data source
    document = get_document_by_id(document_id)

    # Check if the document exists
    if document is None:
        return "Document not found"

    # Process the document or perform any necessary operations
    # ...

    # Return a response or render a template with the document information
    return render_template('document.html', document=document)


@app.route('/some_route')
def some_route():
    # Get the document_id from your data source
    document_id = "123"  # Example document_id as a string

    # Redirect to the document route with the document_id
    return redirect(url_for('document_route', document_id=document_id))


@app.route('/download_document/<document_id>', methods=['GET'])
def download_document(document_id):
    # Retrieve the document information from the database
    cursor = db.connection.cursor()
    query = "SELECT filename, file_path FROM documents WHERE document_id = %s"
    cursor.execute(query, (document_id,))
    document = cursor.fetchone()
    cursor.close()

    if document:
        # Prepare the file path
        file_path = document['file_path']
        filename = document['filename']

        # Check if the file exists
        if os.path.exists(file_path):
            # Prepare the response with appropriate headers
            response = make_response(send_file(file_path, as_attachment=True, attachment_filename=filename))
            return response
        else:
            return "File not found."
    else:
        return "Document not found."
    
    return render_template('download_document.html')

@app.route('/edit_document/<document_id>', methods=['GET', 'POST'])
@login_required
def edit_document(document_id):
    cursor =db.connection.cursor()
    if request.method == 'POST':
        # Retrieve the edited document details from the form
        title = request.form['title']
        access = request.form['access']
        
        # Update the document in the database
        query = "UPDATE Documents SET title = %s, access = %s WHERE id = %s"
        values = (title, access, document_id)
        cursor.execute(query, values)
        mysql.connection.commit()
        
        flash('Document updated successfully', 'success')
        return redirect(url_for('edit_document', document_id=document_id))
    
    # Retrieve the document details from the database
    query = "SELECT * FROM Documents WHERE id = %s"
    cursor.execute(query, (document_id,))
    document = cursor.fetchone()
    cursor.close()
    
    return render_template('edit_document.html', document=document)

@app.route('/send_document', methods=['GET', 'POST'])
@login_required
def send_document():
    if request.method == 'POST':
        recipient = request.form['recipient']
        title = request.form['title']
        description = request.form['description']
        file = request.files['file']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            # Save the document to the uploads folder
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Send the document to the recipient (perform any necessary operations)

            flash('Document sent successfully.')
            return redirect(url_for('user_index'))
        else:
            flash('Invalid file type. Allowed file types are PDF, DOC, DOCX, TXT.')

    return render_template('send_document.html')

# User management
@app.route("/user_management")
def user_management():
    document = []
    # Fetch all user data from the database
    cursor = db.connection.cursor()
    query = "SELECT * FROM Students"
    cursor .execute(query)
    users = cursor.fetchall()
    cursor.close()
    return render_template('user_management.html', Users=users, document=document)
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
        cursor = db.connection.cursor()
        query = "INSERT INTO otp (matric_no, passkey) VALUES (%s, %s)"
        cursor.execute(query, (matric_number, otp))
        mysql.connection.commit()
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
        cursor = mysql.connection.cursor()
        query = "UPDATE Students SET first_name = %s, last_name = %s, department = %s, phone_number = %s WHERE id = %s"
        cursor.execute(query, (first_name, last_name, department, phone_number, user_id))
        mysql.connection.commit()
        cursor.close()
        
        flash('User details updated successfully')
        return redirect(url_for('edit_user'))
    else:
        # Retrieve all users from the database
        cursor = mysql.connection.cursor()
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
            cursor = mysql.connection.cursor()
            for user_id in selected_users:
                query = "DELETE FROM Students WHERE id = %s"
                cursor.execute(query, (user_id,))
            mysql.connection.commit()
            cursor.close()
            
            flash('Selected users deleted successfully')
        elif 'delete_all' in request.form:
            # Delete all users from the database
            cursor = mysql.connection.cursor()
            query = "DELETE FROM Students"
            cursor.execute(query)
            mysql.connection.commit()
            cursor.close()
            
            flash('All users deleted successfully')
        
        return redirect(url_for('delete_user'))
    else:
        # Retrieve all users from the database
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM Students"
        cursor.execute(query)
        users = cursor.fetchall()
        cursor.close()
        
        return render_template('delete_user.html', users=users)

@app.route('/manage_logs')
def manage_logs():
    # Get the logs from your data source
    logs = get_logs()  # Replace with your logic to retrieve logs

    return render_template('manage_logs.html', logs=logs)

def get_logs():
    conn = sqlite3.connect('logs.db')  # Connect to your database
    cursor = conn.cursor()

    # Fetch the logs from the database
    cursor.execute("SELECT username, action, timestamp FROM logs")
    rows = cursor.fetchall()

    # Process the fetched rows into a list of dictionaries
    logs = []
    for row in rows:
        username, action, timestamp = row
        log = {
            'username': username,
            'action': action,
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        logs.append(log)

    conn.close()  # Close the database connection

    return logs

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
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


#Register 
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
            session['matric_no'] = matric_no
            return redirect(url_for('login'))
    return render_template('registeration_user.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    session.pop('logged_in', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))




if __name__ == '__main__':
    app.run(debug=True)


'''app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'lcu_database'''

'''def get_document_id():
    # Retrieve the document id from your data source
    files_dir = 'files'
    files = glob.glob(os.path.join(files_dir, '*.*'))  # Get all files in the directory
    if files:
        document_id = os.path.basename(files[0])  # Get the filename as the document id
        return document_id
    else:
        return None'''

'''def get_document_by_id(document_id):
    # Retrieve the document with the given document_id from your data source
    files_dir = 'files'
    document_path = os.path.join(files_dir, document_id)
    if os.path.exists(document_path):
        return {'document_path': document_path, 'document_id': document_id}
    else:
        return None'''

'''def upload_document():   
    if request.method == 'POST' and 'document' in request.files:
        # Process the uploaded file
        uploaded_file = request.files['document']
        filename = secure_filename(uploaded_file.filename)

        # Save the document to a desired location
        # For example, to save it in a folder called "uploads" in the current directory:
        document_path = f"uploads/{filename}"
        uploaded_file.save(document_path)

        # Store the document information in the database
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO documents (name) VALUES (%s)", [filename])
        conn.commit()
        cursor.close()
        conn.close()

        # Create a document object with relevant information
        document = {
            "filename": filename,
            "path": document_path
        }

        #return render_template('upload_document.html', document=document)
    else :
        flash('Please select a file to upload.')
        #return redirect(url_for('upload_document'))

    # If the request method is GET, simply render the upload_document.html template
    return render_template('upload_document.html')'''