from __future__ import unicode_literals
from __future__ import print_function
from distutils.log import debug
from unittest import result
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash,abort, logging
from flaskext.mysql import MySQL
from functools import wraps
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from pip import main
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from sklearn import tree 
from sklearn import model_selection
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import cross_val_score
from googleplaces import GooglePlaces, types, lang 
from flask_socketio import SocketIO
import pandas as pd 
import numpy as np
import pickle
import re
import os
import random
import hashlib 
import bcrypt
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import nltk
import pybase64
from datetime import date
from sklearn.preprocessing import normalize
from wtforms.fields.html5 import EmailField
import uuid
import user
from flask_mail import Mail, Message
from flask_socketio import SocketIO, emit, send
from flask_cors import CORS
import json
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
CORS(app)
socketio.init_app(app, cors_allowed_origins="*")
users = []

app = Flask(__name__)

port = int(os.environ.get('PORT', 5000))

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'canada$God7972#'

# Enter your database connection details below
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD	'] = ''
app.config['MYSQL_DATABASE_DB'] = 'pharmacat'

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'chalielijalem@gmail.com'
app.config['MAIL_PASSWORD'] = 'kxtgnwrihqqlszay'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True


mail = Mail(app)
# Intialize MySQL
mysql = MySQL(autocommit=True)
mysql.init_app(app)



"""-------------------------------Start of HealthHUB API for developers-------------------------------"""

@app.route('/api/details/<token>',methods=['GET'])
def detailsapi(token):
    tkn = pybase64.b64decode(token)
    r = tkn.decode('utf-8')
    str1 = r.split("(~)")
    username = str1[0]
    password = str1[1]
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM users WHERE Username = %s', [username])
    account = cursor.fetchone()
    details = [
    {
        'ID': account[0],
        'Username': username,
        'Email': account[3], 
        'FullName': account[4],
        'Address': account[5],
        'BloodGroup': account[6],
        'Age': account[7]
    }]
    return jsonify({'Details': details})

@app.route('/api/login/<code>',methods=['GET'])
def loginapi(code):
    code1 = code.split('~')
    username = code1[0]
    password = code1[1]
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM users WHERE Username = %s', [username])
    account = cursor.fetchone()
    if bcrypt.checkpw(password.encode('utf-8'), account[2].encode('utf-8')):
        token = account[8]
        return jsonify({'Token': token})
    return jsonify({'Token': "Invalid Credentials"})

@app.route('/api/diagnosetext/<code>',methods=['GET'])
def diagnosetextapi(code):
    code1 = code.split('~')
    rf=""
    for i in code1:
        rf=rf+i+" "
    filename = 'disease_predict.sav'
    feel = rf
    data = [feel]
    cv = pickle.load(open("vectorizer.pickle", 'rb'))     #Load vectorizer
    loaded_model = pickle.load(open(filename, 'rb'))
    vect=cv.transform(data).toarray()
    p=loaded_model.predict(vect)
    return jsonify({'Disease': p[0]})

@app.route('/api/hospital/<token>',methods=['GET'])
def hospital(token):
    tkn = pybase64.b64decode(token)
    r = tkn.decode('utf-8')
    str1 = r.split("(~)")
    username = str1[0]
    password = str1[1]
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM users WHERE Username = %s', [username])
    account = cursor.fetchone()
    API_KEY = 'Enter your key'
    str1 = str(account[5]).split(",")
    l=""
    for i in range(0,len(str1)):
        l=l+str1[i]+"+"
    send_url = 'https://maps.googleapis.com/maps/api/geocode/json?address='+l+'&key='+API_KEY
    r = requests.get(send_url) 
    j = json.loads(r.text) 
    lat = j['results'][0]['geometry']['location']['lat']
    lon = j['results'][0]['geometry']['location']['lng']


    # Initialising the GooglePlaces constructor 
    google_places = GooglePlaces(API_KEY) 

    query_result = google_places.nearby_search( 
            lat_lng ={'lat': lat, 'lng': lon}, 
            radius = 5000, 
            types =[types.TYPE_HOSPITAL]) 

    places = []
    # Iterate over the search results 
    for place in query_result.places: 
        places.append(place.name)
    return jsonify({'Hospitals': places})

@app.route('/api/symptoms/',methods=['GET'])
def symptoms():
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM symptoms ORDER BY Symptom_Name ASC')
    sym = cursor.fetchall()
    sym1=[]
    for i in sym:
        sym1.append(i)
    symptoms=[]
    for i in range(0,len(sym1)):
        symptoms.append(sym1[i][1])
    return jsonify({'Symptoms': symptoms})
    

@app.route('/api/register/<code>',methods=['GET'])
def registerapi(code):
    code1 = code.split('~')
    username = code1[0]
    password = code1[1]
    email = code1[2]
    full_name = code1[3]
    address = code1[4]
    blood = code1[5]
    age = code1[6]
    msg = ''

    # Check if account exists using MySQL
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM users WHERE Username = %s', (username))
    account = cursor.fetchone()
    # If account exists show error and validation checks
    if account:
        msg = 'Account already exists!'
        return jsonify({'Message': msg})
    elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
        msg = 'Invalid email address!'
        return jsonify({'Message': msg})
    elif not re.match(r'[A-Za-z0-9]+', username):
        msg = 'Username must contain only characters and numbers!'
        return jsonify({'Message': msg})
    elif not username or not password or not email:
        msg = 'Please fill out the form!'
        return jsonify({'Message': msg})
    else:
        comb = username+'(~)'+password
        s = comb.encode()
        s1 = pybase64.b64encode(s)
        api=s1.decode('utf-8')

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('INSERT INTO users VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s)', (username, hashed_password, email, full_name, address, blood, age, api))
        msg = 'You have successfully registered!'
        return jsonify({'Message': msg})
    
@app.route('/api/diagnosesym/<code>',methods=['GET']) #n~symptoms
def diagnosesym(code):
    code1 = code.split('~')
    n = int(code1[0]) 
    l=[]
    for i in range(1,n):
        l.append(code1[i])
    data = pd.read_csv("Manual-Data/Training.csv")

    df = pd.DataFrame(data)
    cols = df.columns
    cols = cols[:-1]
    x = df[cols]
    y = df['prognosis']


    features = cols
    feature_dict = {}
    filename = 'finalized_model.sav'
    for i,f in enumerate(features):
        feature_dict[f] = i

    for i in l:
        s=i
        m=feature_dict[s]
        if (m!=0):
            sample_x = [i/m if i ==m else i*0 for i in range(len(features))]

    loaded_model = pickle.load(open(filename, 'rb'))


    sample_x = np.array(sample_x).reshape(1,len(sample_x))
    p_disease=loaded_model.predict(sample_x)
    answer = p_disease[0]
    cursor1 = mysql.get_db().cursor()
    cursor1.execute('SELECT * FROM medicine WHERE Disease = %s', [answer])
    medicine = cursor1.fetchone()

    cursor2 = mysql.get_db().cursor()
    cursor2.execute('SELECT * FROM doctor_fields WHERE Disease = %s', [answer])
    special = cursor2.fetchone()
    return jsonify({'Disease': answer, 'Medicine': medicine[2], 'Doctor': special[2]})

"""-------------------------------End of HealthHub API for developers-------------------------------"""



"""-------------------------------Start of Web Application-------------------------------"""
    
#Homepage
@app.route('/')
def index():
    return render_template('index.html')


#Dashboard
@app.route('/dashboard')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        if(session['isdoctor']==0):
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
            account = cursor.fetchone()
            cursor1 = mysql.get_db().cursor()
            records = cursor.execute('SELECT * FROM users')
            return render_template('dashboard.html', account = account, num = records,isdoctor=session['isdoctor'])
        else:
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM doctors WHERE ID = %s', [session['id']])
            account = cursor.fetchone()
            cursor1 = mysql.get_db().cursor()
            records = cursor.execute('SELECT * FROM doctors')
            return render_template('doc_dashbord.html', account = account)
        
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))
    # doctor dash bord
@app.route('/dochome')
def dochome():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM doctors WHERE ID = %s', [session['id']])
        account = cursor.fetchone()
        cursor1 = mysql.get_db().cursor()
        records = cursor.execute('SELECT * FROM doctors')
        return render_template('doc_dashbord.html', account = account, num = records,isdoctor=session['isdoctor'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))
    # doctor dash bord

@app.route('/doc_dash')
def doc_dash():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        if(session['isdoctor']==0):
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
        else:
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM doctors WHERE ID = %s', [session['id']])
        account = cursor.fetchone()
        cursor1 = mysql.get_db().cursor()
        records = cursor.execute('SELECT * FROM users')
        return render_template('doc_dashbord.html', account = account, num = records,isdoctor=session['isdoctor'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))
#Patient Login

@app.route('/admin_dash')
def admin_dash():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        if(session['isadmin']==0):
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
        else:
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM admin WHERE ID = %s', [session['id']])
        account = cursor.fetchone()
        cursor = mysql.get_db().cursor()
        records = cursor.execute('SELECT * FROM users')
        return render_template('admin_dashboard.html', account = account, num = records,isadmin=session['isadmin'])
    # User is not loggedin redirect to login page
    return redirect(url_for('adminlogin'))
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE Username = %s', (username))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        # if account:
        if bcrypt.checkpw(password.encode('utf-8'), account[2].encode('utf-8')):
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            session['full_name']=account[5]
            session['api'] = account[8]
            session['isdoctor'] = 0
            x= '1'
            cursor.execute("UPDATE users SET online=%s WHERE ID=%s", (x, account[0]))
            # Redirect to dashboard
           
            return home()
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    flash(msg)
    return render_template('patientlogin.html', msg=msg)

#Patient Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        full_name = request.form['full_name']
        address = request.form['address']
        date = request.form['date']
        blood = request.form['blood']
        # Check if account exists using MySQL
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE Username = %s', (username))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into users table
            apistr = username;
            result = hashlib.md5(apistr.encode()) 
            comb = username+'(~)'+password
            s = comb.encode()
            s1 = pybase64.b64encode(s)
            api=s1.decode('utf-8')
            #print(s1)
            #r=pybase64.b64decode(s)
            #print(r.decode('utf-8'))
            
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute('INSERT INTO users VALUES (NULL, %s, %s, %s, NULL, %s, %s, %s, %s, %s,%s, NULL, NULL, NULL, NULL)', (username, hashed_password, email, full_name, address, blood, date, api,0))
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    flash(msg)
    return render_template('patientlogin.html', msg=msg)
#forget password rest option
@app.route('/reset', methods=['GET','POST'])
def reset():
    return render_template('forget.html')
#Doctor Register
@app.route('/docregister', methods=['GET', 'POST'])
def docregister():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        full_name = request.form['full_name']
        registration_number = request.form['registration_number']
        contact_number = request.form['contact_number']
        spec = request.form['specialization']
        address = request.form['address']

        # Check if account exists using MySQL
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM doctors WHERE Username = %s', (username))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into users table
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            print(username + "\n" + str(hashed_password)+ "\n" + email+ "\n" +full_name+ "\n" +registration_number+ "\n" +contact_number+ "\n" +spec+ "\n" +address)
            cursor.execute('INSERT INTO doctors VALUES (NULL, %s, %s, %s, %s, %s, %s ,%s, %s, %s, %s)', ( username, hashed_password, email, full_name, registration_number, contact_number, "" , spec, address ,0))
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    flash(msg)
    return render_template('doctorlogin.html', msg=msg)

#Doctor Login
@app.route('/doclogin', methods=['GET', 'POST'])
def doclogin():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM doctors WHERE Username = %s', (username))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        # if account:
        
        if bcrypt.checkpw(password.encode('utf-8'), account[2].encode('utf-8')):
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            session['full_name']= account[4]
            session['isdoctor'] = 1
            x = '1'
            cursor.execute("UPDATE doctors SET online=%s WHERE ID=%s", (x, account[0]))
            # Redirect to home page
            return doc_dash()
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    flash(msg)
    return render_template('doctorlogin.html', msg=msg)

#admin page 
@app.route('/adminregister', methods=['GET', 'POST'])
def adminregister():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        full_name = request.form['full_name']
        registration_number = request.form['registration_number']
        contact_number = request.form['contact_number']
        #spec = request.form['specialization']
        address = request.form['address']

        # Check if account exists using MySQL
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM admin WHERE Username = %s', (username))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into users table
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            print(username + "\n" + str(hashed_password)+ "\n" + email+ "\n" +full_name+ "\n" +registration_number+ "\n" +contact_number+ "\n" +address)
            cursor.execute('INSERT INTO admin VALUES (NULL, %s, %s, %s, %s, %s,%s, %s)', ( username, hashed_password, email, full_name, registration_number, contact_number, address ))
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    flash(msg)
    return render_template('adminlogin.html', msg=msg)

#admin login page 
@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM admin WHERE Username = %s', (username))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        # if account:
        if bcrypt.checkpw(password.encode('utf-8'), account[2].encode('utf-8')):
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            session['isadmin'] = 1
            # Redirect to home page
            return admin_dash()
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    flash(msg)
    return render_template('adminlogin.html', msg=msg)
    
#BMI for the dashboard(Written by Mayank)
@app.route('/bmi',methods=['GET', 'POST'])
def bmi():
    if 'loggedin' in session:
        result=0
        h=0
        w=0
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE Username = %s', [session['username']])
        account = cursor.fetchone()
        if request.method=='POST':
            h=float(request.form["height"])
            h=float(h)
            w=request.form["weight"]
            w=float(w)
            result=w/(h*h)
            result=round(result,2)
        return render_template('bmi.html',ans=result,account=account,height=h,weight=w) 
    return redirect(url_for('login'))
@app.route("/consultation")
def consultation():
    if 'loggedin' in session:
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
        account = cursor.fetchone()
        return render_template('consultation.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))
  
 
#Diagnose based on Symptoms First Step
@app.route('/diagnose')
def diagnose():
    # Check if user is loggedin
    if 'loggedin' in session:
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
        account = cursor.fetchone()
        return render_template('diagnose.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))
#Health Status
@app.route('/healthstatus')
def healthstatus():
    # Check if user is loggedin
    if 'loggedin' in session:
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
        account = cursor.fetchone()
        channel=account[11]
        temp=account[12]
        hum=account[13]
        puls=account[14]
        return render_template('healthstatus.html', account=account,channel=channel, temp=temp, hum=hum, puls=puls)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))
#Myaccount Details
@app.route('/myaccount')
def myaccount():
    # Check if user is loggedin
    if 'loggedin' in session:
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
        account = cursor.fetchone()
        return render_template('myaccount.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))
#Diagnose based on Symptoms Second Step
@app.route('/diagnoseproceed',methods=['GET','POST'])
def diagnoseproceed():
    # Check if user is loggedin
    if 'loggedin' in session:
        
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
        account = cursor.fetchone()
        cursor.execute('SELECT * FROM symptoms ORDER BY Symptom_Name ASC')
        sym = cursor.fetchall()
        sym1=[]
        for i in sym:
            sym1.append(i)
        symptoms=[]
        #return str(sym1[0])
        for i in sym1:
            #return str(i[1])
            k=str(i[1]).split("_")
            l=""
            if(len(k)>1):
                for i in k:
                    l=l+i.capitalize()+" "
                symptoms.append(l)
            else:
                l=l+k[0].capitalize()
                symptoms.append(l)
        
        if(request.method == 'POST'):
            n = int(request.form['n'])
            return render_template('diagnoseproceed.html', account=account,n=n,symptoms=symptoms,sym1=sym1)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

#Diagnose based on Symptoms Third Step
@app.route('/diagnosefinal',methods=['GET','POST'])
def diagnosefinal():
    # Check if user is loggedin
    if 'loggedin' in session:
        
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
        account = cursor.fetchone()
        
        
        if(request.method == 'POST'):
            n = int(request.form['n'])
            l=[]
            data = pd.read_csv("Manual-Data/Training.csv")

            df = pd.DataFrame(data)
            cols = df.columns
            cols = cols[:-1]
            x = df[cols]
            y = df['prognosis']
            
            
            features = cols
            feature_dict = {}
            filename = 'pickle_model.pkl'
            for i,f in enumerate(features):
                feature_dict[f] = i
            
            for i in range(0,n):
                l.append(request.form['sym'+str(i)])

            X = [0]*132    
            for i in l:
                s=i
                m=feature_dict[s]
                if (m!=0):
                    print("\n\n")
                    print(m)
                    #print("\n\n")
                    sample_x = [i/m if i ==m else i*0 for i in range(len(features))]
                    X[m] = 1
                
            loaded_model = pickle.load(open(filename, 'rb'))
            
            print("\n\n")
            print(sample_x)
            print("\n\n")
            print(len(sample_x))
            print("\n\n")
            print(X)
            print("\n\n")

            sample_x = np.array(sample_x).reshape(1,len(sample_x))
            X = np.array(X).reshape(1,len(X))
            p_disease=loaded_model.predict(sample_x)
            p_disease2=loaded_model.predict(X)
            answer = p_disease[0]
            answer2 = p_disease2[0]
            print(answer2)
            cursor1 = mysql.get_db().cursor()
            cursor1.execute('SELECT * FROM medicine WHERE Disease = %s', [answer2])
            medicine = cursor1.fetchone()
            
            cursor2 = mysql.get_db().cursor()
            cursor2.execute('SELECT * FROM doctor_fields WHERE Disease = %s', [answer2])
            special = cursor2.fetchone()
            return render_template('diagnosefinal.html', account=account,n=n,symptoms=l,answer=answer2,medicine=medicine[2],special=special[2])
           
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

#Diagnose based on Natural Language
@app.route('/diagnosedetails',methods=['GET','POST'])
def diagnosedetails():
    # Check if user is loggedin
    if 'loggedin' in session:
        
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
        account = cursor.fetchone()
        
        
        if(request.method == 'POST'):
            filename = 'disease_predict.sav'
            feel = request.form['feel']
            data = [feel]
            cv = pickle.load(open("vectorizer.pickle", 'rb'))     #Load vectorizer
            loaded_model = pickle.load(open(filename, 'rb'))
            vect=cv.transform(data).toarray()
            p=loaded_model.predict(vect)
            return render_template('diagnoseanswerNLP.html',account=account,ans=p[0])
        else:
            return render_template('diagnoseNLP.html',account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


#Hospitals near to the Address using GeoCoding
@app.route('/hospitals')
def hospitals():
    # Check if user is loggedin
    if 'loggedin' in session:
        
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
        account = cursor.fetchone()
        if(account is None):
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM doctors WHERE ID = %s', [session['id']])
            account = cursor.fetchone()
            address = account[9]
        else:
            address = account[5]
        # enter your api key here 
        API_KEY = 'AIzaSyCn8Lj3fta07gTzYzRSPQ0NjLaB059TyOE'
        str1 = str(address).split(",")
        l=""
        for i in range(0,len(str1)):
            l=l+str1[i]+"+"
        send_url = 'https://maps.googleapis.com/maps/api/geocode/json?address='+l+'&key='+API_KEY 
        r = requests.get(send_url) 
        j = json.loads(r.text) 
        lat = j['results'][0]['geometry']['location']['lat']
        lon = j['results'][0]['geometry']['location']['lng']


        # Initialising the GooglePlaces constructor 
        google_places = GooglePlaces(API_KEY) 

        query_result = google_places.nearby_search( 
                lat_lng ={'lat': lat, 'lng': lon}, 
                radius = 5000, 
                types =[types.TYPE_HOSPITAL]) 

        places = []
        # Iterate over the search results 
        for place in query_result.places: 
            # print(type(place)) 
            # place.get_details() 
            places.append(place.name) 
            #print("Latitude", place.geo_location['lat']) 
            #print("Longitude", place.geo_location['lng']) 
        return render_template('hospitals.html', places=places, account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

#Set Hospital
@app.route('/hospitalset',methods=['GET', 'POST'])
def hospitalset():
    # Check if user is loggedin
    if 'loggedin' in session:
        
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM doctors WHERE ID = %s', [session['id']])
        account = cursor.fetchone()
        # enter your api key here 
        API_KEY = 'Enter your key'
        str1 = str(account[9]).split(",")
        l=""
        for i in range(0,len(str1)):
            l=l+str1[i]+"+"
        send_url = 'https://maps.googleapis.com/maps/api/geocode/json?address='+l+'&key='+API_KEY
        r = requests.get(send_url) 
        j = json.loads(r.text) 
        lat = j['results'][0]['geometry']['location']['lat']
        lon = j['results'][0]['geometry']['location']['lng']


        # Initialising the GooglePlaces constructor 
        google_places = GooglePlaces(API_KEY) 

        query_result = google_places.nearby_search( 
                lat_lng ={'lat': lat, 'lng': lon}, 
                radius = 5000, 
                types =[types.TYPE_HOSPITAL]) 

        places = []
        # Iterate over the search results 
        for place in query_result.places: 
            places.append(place.name) 
            
        if(request.method == 'POST'):
            hname = request.form['hname']
            cursor = mysql.get_db().cursor()
            cursor.execute('UPDATE doctors SET Hospital_Name= %s WHERE ID= %s', [hname,session['id']])
            return render_template('dashboard.html', account=account)
        return render_template('hospitalset.html', places=places, account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

#Book an Appointment 
@app.route('/book',methods=['GET', 'POST'])
def book():
    # Check if user is loggedin
    if 'loggedin' in session:
        
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
        account = cursor.fetchone()
        cur = mysql.get_db().cursor()
        cur.execute("SELECT * FROM doctors")
        appinfo = cur.fetchall()
        
        speci = set()
        for m in appinfo:
            speci.add(m[8])
        
        return render_template('bookhome.html', speci=speci, account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/bookh',methods=['GET', 'POST'])
def bookh():
    # Check if user is loggedin
    if 'loggedin' in session:
        
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
        account = cursor.fetchone()
        cur = mysql.get_db().cursor()
        cur.execute("SELECT * FROM doctors")
        appinfo = cur.fetchall()
        if(request.method == 'POST'):
            fname = request.form['fname']
            session['speci'] = fname
            cursor11 = mysql.get_db().cursor()
            cursor11.execute('SELECT * FROM doctors WHERE Specialization= %s', [fname])
            doc = cursor11.fetchall()
                
            return render_template('book.html', account=account,doc=doc)
        return render_template('bookhome.html', appinfo=appinfo, account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/bookhh',methods=['GET', 'POST'])
def bookhh():
    # Check if user is loggedin
    if 'loggedin' in session:
        
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
        account = cursor.fetchone()
        cur = mysql.get_db().cursor()
        cur.execute("SELECT * FROM doctors")
        appinfo = cur.fetchall()
        if(request.method == 'POST'):
            fname = request.form['fname']
            date = request.form['date']
            time = request.form['time']
            cursor11 = mysql.get_db().cursor()
            cursor11.execute('SELECT * FROM doctors WHERE Full_Name= %s', [fname])
            doc = cursor11.fetchone()
            cursor1 = mysql.get_db().cursor()
            cursor1.execute('INSERT INTO booking VALUES (NULL, %s, %s, %s, %s, %s)', ( doc[0], session['id'], date, time, 0))
            cursor2 = mysql.get_db().cursor()    
            cursor2.execute('SELECT * FROM booking WHERE Patient_ID= %s', [session['id']])
            l = cursor2.fetchall()
            arr = []
            for i in l:
                cursor3 = mysql.get_db().cursor()    
                cursor3.execute('SELECT * FROM doctors WHERE ID= %s', [i[1]])
                doc = cursor3.fetchone()
                arr.append([doc[4],doc[9]])
                
            return render_template('appointments.html', account=account,l=l,arr=arr)
        return render_template('book.html', appinfo=appinfo, account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))
#Appointments page for Patients
@app.route('/appointments',methods=['GET', 'POST'])
def appointments():
    # Check if user is loggedin
    if 'loggedin' in session:
        
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
        account = cursor.fetchone()
        if(account is None):
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM doctors WHERE ID = %s', [session['id']])
            account = cursor.fetchone()
            address = account[9]
        else:
            address = account[5]
            
        cursor2 = mysql.get_db().cursor()    
        cursor2.execute('SELECT * FROM booking WHERE Patient_ID= %s', [session['id']])
        l = cursor2.fetchall()
        arr = []
        for i in l:
            cursor3 = mysql.get_db().cursor()    
            cursor3.execute('SELECT * FROM doctors WHERE ID= %s', [i[1]])
            doc = cursor3.fetchone()
            arr.append([doc[4],doc[9]])
            
        return render_template('appointments.html', account=account,l=l,arr=arr)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/curappointment',methods=['GET', 'POST'])
def curappointment():
    # Check if user is loggedin
    if 'loggedin' in session:
        
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM doctors WHERE ID = %s', [session['id']])
        account = cursor.fetchone()
        if(account is None):
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
            account = cursor.fetchone()
            address = account[5]
        else:
            address = account[9]
            
        cursor2 = mysql.get_db().cursor()    
        cursor2.execute('SELECT * FROM booking WHERE Doctor_ID= %s', [session['id']])
        l = cursor2.fetchall()
        arr = []
        for i in l:
            cursor3 = mysql.get_db().cursor()    
            cursor3.execute('SELECT * FROM users WHERE ID= %s', [i[2]])
            doc = cursor3.fetchone()
            arr.append([doc[5],doc[6]])
            
        return render_template('viewappointments.html', account=account,l=l,arr=arr)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/cancel_app/<string:id>', methods=['POST'])
def cancel_app(id):
    #create cursor
    cur = mysql.get_db().cursor()
    cur.execute("DELETE FROM booking WHERE Record_ID = %s", [id])
    mysql.get_db().commit()
    cur.close()
    #flash('Appointment is canceled', 'success')
    return redirect(url_for('curappointment'))

@app.route('/approve_app/<string:id>', methods=['POST'])
def approve_app(id):
    #create cursor
    cur = mysql.get_db().cursor()
    cur.execute("UPDATE booking SET Status=1 WHERE Record_ID = %s", [id])
    mysql.get_db().commit()
    cur.close()
    #flash('Appointment is canceled', 'success')
    return redirect(url_for('curappointment'))

@app.route('/cancelp_app/<string:id>', methods=['POST'])
def cancelp_app(id):
    #create cursor
    cur = mysql.get_db().cursor()
    cur.execute("DELETE FROM booking WHERE Record_ID = %s", [id])
    mysql.get_db().commit()
    cur.close()
    #flash('Appointment is canceled', 'success')
    return redirect(url_for('appointments'))

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, *kwargs)
        else:
            flash('Unauthorized, Please logged in', 'danger')
            return redirect(url_for('login'))
    return wrap


def not_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            flash('Unauthorized, You logged in', 'danger')
            return redirect(url_for('index'))
        else:
            return f(*args, *kwargs)
    return wrap



class MessageForm(Form):    # Create Message Form
    body = StringField('', [validators.length(min=1)], render_kw={'autofocus': True})

@app.route('/chatting/<string:id>', methods=['GET', 'POST'])
def chatting(id):
    if 'loggedin' in session:
        
        form = MessageForm(request.form)
        # Create cursor
        cur = mysql.get_db().cursor()

        # lid name
        get_result = cur.execute("SELECT * FROM doctors WHERE ID=%s", [id])
        l_data = cur.fetchone()
        if get_result > 0:
            session['name'] = l_data[4]
            uid = session['id']
            session['lid'] = id

            if request.method == 'POST' and form.validate():
                txt_body = form.body.data
                # Create cursor
                cur = mysql.get_db().cursor()
                cur.execute("INSERT INTO messages(body, msg_by, msg_to) VALUES(%s, %s, %s)",
                            (txt_body, session['full_name'], session['name']))
                # Commit cursor
                mysql.get_db().commit()

            # Get users
            cur.execute("SELECT * FROM doctors")
            users = cur.fetchall()

            # Close Connection
            cur.close()
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
            account = cursor.fetchone()
            return render_template('chat_room.html', users=users, form=form, account=account)
        else:
            flash('No permission!', 'danger')
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

@app.route('/chattingh/<string:id>', methods=['GET', 'POST'])
def chattingh(id):
    if 'loggedin' in session:
        
        form = MessageForm(request.form)
        # Create cursor
        cur = mysql.get_db().cursor()

        # lid name
        get_result = cur.execute("SELECT * FROM users WHERE ID=%s", [id])
        l_data = cur.fetchone()
        if get_result > 0:
            session['name'] = l_data[5]
            uid = session['id']
            session['lid'] = id

            if request.method == 'POST' and form.validate():
                txt_body = form.body.data
                # Create cursor
                cur = mysql.get_db().cursor()
                cur.execute("INSERT INTO messages(body, msg_by, msg_to) VALUES(%s, %s, %s)",
                            (txt_body, uid, id))
                # Commit cursor
                mysql.get_db().commit()

            # Get users
            cur.execute("SELECT * FROM doctors")
            users = cur.fetchall()

            # Close Connection
            cur.close()
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
            account = cursor.fetchone()
            return render_template('chat_roomhome.html', users=users, form=form, account=account)
        else:
            flash('No permission!', 'danger')
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))


@app.route('/chats', methods=['GET', 'POST'])
def chats():
    if 'loggedin' in session:
        id = session['name']
        uid = session['full_name']
        # Create cursor
        cur = mysql.get_db().cursor()
        # Get message here
        cur.execute("SELECT * FROM messages WHERE (msg_by=%s AND msg_to=%s) OR (msg_by=%s AND msg_to=%s) "
                    "ORDER BY id ASC", (uid, id, id, uid))
        chats = cur.fetchall()
        # Close Connection
        cur.close()
        return render_template('chats.html', chats=chats,)
    return redirect(url_for('login'))


@app.route('/docchatting/<string:id>', methods=['GET', 'POST'])
def docchatting(id):
    if 'loggedin' in session:
        
        form = MessageForm(request.form)
        # Create cursor
        cur = mysql.get_db().cursor()

        # lid name
        get_result = cur.execute("SELECT * FROM users WHERE ID=%s", [id])
        l_data = cur.fetchone()
        if get_result > 0:
            session['name'] = l_data[5]
            uid = session['id']
            session['lid'] = id

            if request.method == 'POST' and form.validate():
                txt_body = form.body.data
                # Create cursor
                cur = mysql.get_db().cursor()
                cur.execute("INSERT INTO messages(body, msg_by, msg_to) VALUES(%s, %s, %s)",
                            (txt_body, session['full_name'], session['name']))
                # Commit cursor
                mysql.get_db().commit()
            
            curl = mysql.get_db().cursor()

            curl.execute("SELECT * FROM messages Where msg_to=%s", [session['full_name']])
            message = curl.fetchall()
            patient = set()
            for m in message:
                patient.add(m[2])
            # Get users
            cur.execute("SELECT * FROM users")
            users = cur.fetchall()

            # Close Connection
            cur.close()
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM doctors WHERE ID = %s', [session['id']])
            account = cursor.fetchone()
            return render_template('docchat_room.html', users=users, form=form, account=account, patient=patient)
        else:
            flash('No permission!', 'danger')
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))


@app.route('/docchattingh/<string:id>', methods=['GET', 'POST'])
def docchattingh(id):
    if 'loggedin' in session:
        
        form = MessageForm(request.form)
        # Create cursor
        cur = mysql.get_db().cursor()

        # lid name
        get_result = cur.execute("SELECT * FROM doctors WHERE ID=%s", [id])
        l_data = cur.fetchone()
        if get_result > 0:
            session['name'] = l_data[4]
            uid = session['id']
            session['lid'] = id

            if request.method == 'POST' and form.validate():
                txt_body = form.body.data
                # Create cursor
                cur = mysql.get_db().cursor()
                cur.execute("INSERT INTO messages(body, msg_by, msg_to) VALUES(%s, %s, %s)",
                            (txt_body, uid, id))
                # Commit cursor
                mysql.get_db().commit()
            curl = mysql.get_db().cursor()
            curl.execute("SELECT * FROM messages Where msg_to=%s", [session['name']])
            message = curl.fetchall()
            person = set()
            for m in message:
                person.add(m[2])
            # Get users
            cur.execute("SELECT * FROM users")
            users = cur.fetchall()

            # Close Connection
            cur.close()
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM doctors WHERE ID = %s', [session['id']])
            account = cursor.fetchone()
            return render_template('docchat_roomhome.html', users=users, form=form, account=account, person=person)
        else:
            flash('No permission!', 'danger')
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))
@app.route('/docsensor/<string:id>', methods=['GET', 'POST'])
def docsensor(id):
    if 'loggedin' in session:
        
        form = MessageForm(request.form)
        # Create cursor
        cur = mysql.get_db().cursor()

        # lid name
        get_result = cur.execute("SELECT * FROM users WHERE ID=%s", [id])
        l_data = cur.fetchone()
        if get_result > 0:
            session['name'] = l_data[5]
            uid = session['id']
            session['lid'] = id
            channel=l_data[11]
            temp=l_data[12]
            hum=l_data[13]
            puls=l_data[14]

            curl = mysql.get_db().cursor()

            curl.execute("SELECT * FROM messages Where msg_to=%s", [session['full_name']])
            message = curl.fetchall()
            patient = set()
            for m in message:
                patient.add(m[2])


            # Close Connection
            curl.close()

            # Get users
            cur.execute("SELECT * FROM users")
            users = cur.fetchall()

            # Close Connection
            cur.close()
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM doctors WHERE ID = %s', [session['id']])
            account = cursor.fetchone()
            return render_template('docsensor.html', users=users, form=form, account=account, channel=channel, temp=temp, hum=hum, puls=puls, patient=patient)
        else:
            flash('No permission!', 'danger')
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))


@app.route('/docsensorh/<string:id>', methods=['GET', 'POST'])
def docsensorh(id):
    if 'loggedin' in session:
        
        # Create cursor
        cur = mysql.get_db().cursor()
        curl = mysql.get_db().cursor()

        # lid name
        get_result = cur.execute("SELECT * FROM doctors WHERE ID=%s", [id])
        l_data = cur.fetchone()
        if get_result > 0:
            session['name'] = l_data[4]
            uid = session['id']
            session['lid'] = id

            # Get users
            curl.execute("SELECT * FROM messages Where msg_to=%s", [session['name']])
            message = curl.fetchall()
            person = set()
            for m in message:
                person.add(m[2])


            # Close Connection
            curl.close()
            cur.execute("SELECT * FROM users")
            users = cur.fetchall()

            # Close Connection
            
            cur.close()
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM doctors WHERE ID = %s', [session['id']])
            account = cursor.fetchone()
            return render_template('docsensorhome.html', users=users,message=message ,account=account,person=person)
        else:
            flash('No permission!', 'danger')
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))


#Recommendation
@app.route('/recommending/<string:id>', methods=['GET', 'POST'])
def recommending(id):
    if 'loggedin' in session:
        
        form = MessageForm(request.form)
        # Create cursor
        cur = mysql.get_db().cursor()

        # lid name
        get_result = cur.execute("SELECT * FROM doctors WHERE ID=%s", [id])
        l_data = cur.fetchone()
        if get_result > 0:
            session['name'] = l_data[4]
            uid = session['id']
            session['lid'] = id

            if request.method == 'POST' and form.validate():
                txt_body = form.body.data
                # Create cursor
                cur = mysql.get_db().cursor()
                cur.execute("INSERT INTO recommendations(body, recommend_by, recommend_to) VALUES(%s, %s, %s)",
                            (txt_body, session['full_name'], session['name']))
                # Commit cursor
                mysql.get_db().commit()

            # Get users
            cur.execute("SELECT * FROM doctors")
            users = cur.fetchall()

            # Close Connection
            cur.close()
            curo = mysql.get_db().cursor()
            curo.execute("SELECT * FROM recommendations where recommend_by=%s", [session['name']])
            recom = curo.fetchall()
            curo.close()
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
            account = cursor.fetchone()
            return render_template('recommendation__room.html',recom=recom, users=users, form=form, account=account)
        else:
            flash('No permission!', 'danger')
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

@app.route('/recommendingh/<string:id>', methods=['GET', 'POST'])
def recommendingh(id):
    if 'loggedin' in session:
        
        form = MessageForm(request.form)
        # Create cursor
        cur = mysql.get_db().cursor()

        # lid name
        get_result = cur.execute("SELECT * FROM users WHERE ID=%s", [id])
        l_data = cur.fetchone()
        if get_result > 0:
            session['name'] = l_data[5]
            uid = session['id']
            session['lid'] = id

            if request.method == 'POST' and form.validate():
                txt_body = form.body.data
                # Create cursor
                cur = mysql.get_db().cursor()
                cur.execute("INSERT INTO recommendations(body, recommend_by, recommend_to) VALUES(%s, %s, %s)",
                            (txt_body, uid, id))
                # Commit cursor
                mysql.get_db().commit()

            # Get users
            cur.execute("SELECT * FROM doctors")
            users = cur.fetchall()

            # Close Connection
            cur.close()
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
            account = cursor.fetchone()
            return render_template('recommendation_roomhome.html', users=users, form=form, account=account)
        else:
            flash('No permission!', 'danger')
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))


@app.route('/recommends', methods=['GET', 'POST'])
def recommends():
    if 'loggedin' in session:
        id = session['name']
        uid = session['full_name']
        # Create cursor
        cur = mysql.get_db().cursor()
        # Get message here
        cur.execute("SELECT * FROM recommendations WHERE (recommend_by=%s AND recommend_to=%s) OR (recommend_by=%s AND recommend_to=%s) "
                    "ORDER BY id ASC", (uid, id, id, uid))
        chats = cur.fetchall()
        # Close Connection
        cur.close()
        return render_template('recommends.html', chats=chats,)
    return redirect(url_for('login'))


@app.route('/docrecommending/<string:id>', methods=['GET', 'POST'])
def docrecommending(id):
    if 'loggedin' in session:
        
        form = MessageForm(request.form)
        # Create cursor
        cur = mysql.get_db().cursor()

        # lid name
        get_result = cur.execute("SELECT * FROM users WHERE ID=%s", [id])
        l_data = cur.fetchone()
        if get_result > 0:
            session['name'] = l_data[5]
            uid = session['id']
            session['lid'] = id

            if request.method == 'POST' and form.validate():
                txt_body = form.body.data
                # Create cursor
                cur = mysql.get_db().cursor()
                cur.execute("INSERT INTO recommendations(body, recommend_by, recommend_to) VALUES(%s, %s, %s)",
                            (txt_body, session['full_name'], session['name']))
                # Commit cursor
                mysql.get_db().commit()

            curl = mysql.get_db().cursor()

            curl.execute("SELECT * FROM messages Where msg_to=%s", [session['full_name']])
            message = curl.fetchall()
            patient = set()
            for m in message:
                patient.add(m[2])


            # Close Connection
            curl.close()
            # Get users
            cur.execute("SELECT * FROM users")
            users = cur.fetchall()

            # Close Connection
            cur.close()
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM doctors WHERE ID = %s', [session['id']])
            account = cursor.fetchone()
            return render_template('docrecommendation_room.html', users=users, form=form, account=account, patient=patient)
        else:
            flash('No permission!', 'danger')
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))


@app.route('/docrecommendingh/<string:id>', methods=['GET', 'POST'])
def docrecommendingh(id):
    if 'loggedin' in session:
        
        form = MessageForm(request.form)
        # Create cursor
        cur = mysql.get_db().cursor()

        # lid name
        get_result = cur.execute("SELECT * FROM doctors WHERE ID=%s", [id])
        l_data = cur.fetchone()
        if get_result > 0:
            session['name'] = l_data[4]
            uid = session['id']
            session['lid'] = id

            if request.method == 'POST' and form.validate():
                txt_body = form.body.data
                # Create cursor
                cur = mysql.get_db().cursor()
                cur.execute("INSERT INTO recommendations(body, recommend_by, recommend_to) VALUES(%s, %s, %s)",
                            (txt_body, uid, id))
                # Commit cursor
                mysql.get_db().commit()
            
            curl = mysql.get_db().cursor()
            curl.execute("SELECT * FROM messages Where msg_to=%s", [session['name']])
            message = curl.fetchall()
            person = set()
            for m in message:
                person.add(m[2])

            # Get users
            cur.execute("SELECT * FROM users")
            users = cur.fetchall()

            # Close Connection
            cur.close()
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM doctors WHERE ID = %s', [session['id']])
            account = cursor.fetchone()
            return render_template('docrecommendation_roomhome.html', users=users, form=form, account=account, person=person)
        else:
            flash('No permission!', 'danger')
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

#ADMin functions 
@app.route('/viewuser')
def view():
   # data = db.read(None)
    cur = mysql.get_db().cursor()
    cur.execute('SELECT * FROM users')
    data = cur.fetchall()
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM admin WHERE Username = %s', [session['username']])
    account = cursor.fetchone()

    return render_template('view.html', data = data,account=account)
@app.route('/viewdoctor')
def viewdoctor():
   # data = db.read(None)
    cur = mysql.get_db().cursor()
    cur.execute('SELECT * FROM doctors')
    data = cur.fetchall()
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM admin WHERE Username = %s', [session['username']])
    account = cursor.fetchone()

    return render_template('viewdoc.html', data = data,account=account)
@app.route('/add/')
def add():
    #data=db.insert(request.form)
    cur = mysql.get_db().cursor()
    cur.execute('SELECT * FROM users')
    data = cur.fetchall()
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM admin WHERE Username = %s', [session['username']])
    account = cursor.fetchone()
    return render_template('add.html', data = data,account=account)

@app.route('/adduser', methods = ['POST', 'GET'])
def adduser():
    #data=db.insert(request.form)
    cur = mysql.get_db().cursor()
    cur.execute('SELECT * FROM users')
    data = cur.fetchall()
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM admin WHERE Username = %s', [session['username']])
    account = cursor.fetchone()
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        full_name = request.form['full_name']
        address = request.form['address']
        date = request.form['date']
        blood = request.form['blood']
        # Check if account exists using MySQL
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE Username = %s', (username))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into users table
            apistr = username;
            result = hashlib.md5(apistr.encode()) 
            comb = username+'(~)'+password
            s = comb.encode()
            s1 = pybase64.b64encode(s)
            api=s1.decode('utf-8')
            #print(s1)
            #r=pybase64.b64decode(s)
            #print(r.decode('utf-8'))
            curs = mysql.get_db().cursor()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            curs.execute('INSERT INTO users VALUES (NULL, %s, %s, %s, NULL, %s, %s, %s, %s, %s,%s, NULL, NULL, NULL, NULL)', (username, hashed_password, email, full_name, address, blood, date, api,0))
            msg = 'User successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    
    flash(msg)
    return redirect(url_for('view', data = data,account=account))

@app.route('/update/<int:ID>/')
def update(ID):
    #data = db.read(ID)
    cur = mysql.get_db().cursor()
    cur.execute("SELECT * FROM users WHERE ID=%s", [ID])
    data = cur.fetchall()
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM admin WHERE Username = %s', [session['username']])
    account = cursor.fetchone()

    if len(data) == 0:
        return redirect(url_for('view', data = data,account=account))
    else:
        session['update'] = ID
        return render_template('update.html', data = data,account=account)

@app.route('/updateuser', methods = ['POST'])
def updateuser():
    cur = mysql.get_db().cursor()
    cur.execute('SELECT * FROM users')
    data = cur.fetchall()
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM admin WHERE Username = %s', [session['username']])
    account = cursor.fetchone()
    if request.method == 'POST' and request.form['update']:
        cursor.execute("UPDATE users set Username = %s, Email = %s, Full_Name= %s, Address= %s, Blood_Group=%s, Age = %s where ID = %s",
                           (request.form['Username'], request.form['Email'],request.form['Full_Name'],request.form['Address'],request.form['Blood_Group'],request.form['Age'],session['update']))

        flash('A user has been updated')

        session.pop('update', None)

        return redirect(url_for('view', data = data,account=account))
    else:
        return redirect(url_for('view', data = data,account=account))

@app.route('/delete/<int:ID>/')
def delete(ID):
    #data = db.read(ID);
    cur = mysql.get_db().cursor()
    cur.execute("SELECT * FROM users WHERE ID=%s", [ID])
    data = cur.fetchall()
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM admin WHERE Username = %s', [session['username']])
    account = cursor.fetchone()

    if len(data) == 0:
        return redirect(url_for('view', data = data,account=account))
    else:
        session['delete'] = ID
        return render_template('delete.html', data = data,account=account)

@app.route('/deleteuser', methods = ['POST'])
def deleteuser():
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM admin WHERE Username = %s', [session['username']])
    account = cursor.fetchone()
    if request.method == 'POST' and request.form['delete']:

        cur = mysql.get_db().cursor()
        cur.execute("SELECT * FROM users")
        data = cur.fetchall()
        cursor.execute("DELETE FROM users where ID = %s", (session['delete']))
        flash('A user has been deleted')

        session.pop('delete', None)

        return redirect(url_for('view'))
    else:
        return redirect(url_for('view'))


@app.route('/addoc/')
def addoc():
    cur = mysql.get_db().cursor()
    cur.execute('SELECT * FROM doctors')
    data = cur.fetchall()
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM admin WHERE Username = %s', [session['username']])
    account = cursor.fetchone()
    return render_template('adddoc.html', data = data,account=account)

@app.route('/adddoc', methods = ['POST', 'GET'])
def adddoc():
    cur = mysql.get_db().cursor()
    cur.execute('SELECT * FROM doctors')
    data = cur.fetchall()
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM admin WHERE Username = %s', [session['username']])
    account = cursor.fetchone()
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        full_name = request.form['full_name']
        registration_number = request.form['registration_number']
        contact_number = request.form['contact_number']
        spec = request.form['specialization']
        address = request.form['address']

        # Check if account exists using MySQL
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM doctors WHERE Username = %s', (username))
        accou = cursor.fetchone()
        # If account exists show error and validation checks
        if accou:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into users table
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            print(username + "\n" + str(hashed_password)+ "\n" + email+ "\n" +full_name+ "\n" +registration_number+ "\n" +contact_number+ "\n" +spec+ "\n" +address)
            cursor.execute('INSERT INTO doctors VALUES (NULL, %s, %s, %s, %s, %s, %s ,%s, %s, %s, %s)', ( username, hashed_password, email, full_name, registration_number, contact_number, "" , spec, address ,0))
            msg = 'Doctor successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    flash(msg)
    return redirect(url_for('viewdoctor', data = data,account=account))

@app.route('/updatedc/<int:ID>/')
def updatedc(ID):
    cur = mysql.get_db().cursor()
    cur.execute("SELECT * FROM doctors WHERE ID=%s", [ID])
    data = cur.fetchall()
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM admin WHERE Username = %s', [session['username']])
    account = cursor.fetchone()

    if len(data) == 0:
        return redirect(url_for('viewdoctor', data = data,account=account))
    else:
        session['update'] = ID
        return render_template('updatedoc.html', data = data,account=account)

@app.route('/updatedoc', methods = ['POST'])
def updatedoc():
    cur = mysql.get_db().cursor()
    cur.execute('SELECT * FROM doctors')
    data = cur.fetchall()
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM admin WHERE Username = %s', [session['username']])
    account = cursor.fetchone()
    if request.method == 'POST' and request.form['update']:
        #cursor.execute("UPDATE doctors set Username = %s, Email = %s, Full_Name= %s, Registration_Number= %s, Contact_Number=%s,  Specialization = %s, Address = %s where ID = %s",
         #                  (request.form['Username'], request.form['Email'],request.form['Full_Name'],request.form['registration_number'],request.form['contact_number'],request.form['specialization'],request.form['address'],session['update']))
        cursor.execute("UPDATE doctors set Username = %s, Email = %s, Full_Name= %s, Address = %s, Registration_Number= %s, Contact_Number=%s,  Specialization = %s where ID = %s",
                           (request.form['Username'], request.form['Email'], request.form['Full_Name'],request.form['Address'], request.form['registration_number'],request.form['contact_number'],request.form['specialization'], session['update']))
        flash('A doctor has been updated')

        session.pop('update', None)

        return redirect(url_for('viewdoctor', data = data,account=account))
    else:
        return redirect(url_for('viewdoctor', data = data,account=account))

@app.route('/deletedo/<int:ID>/')
def deletedc(ID):
    cur = mysql.get_db().cursor()
    cur.execute("SELECT * FROM doctors WHERE ID=%s", [ID])
    data = cur.fetchall()
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM admin WHERE Username = %s', [session['username']])
    account = cursor.fetchone()

    if len(data) == 0:
        return redirect(url_for('viewdoctor', data = data,account=account))
    else:
        session['delete'] = ID
        return render_template('deletedoc.html', data = data,account=account)

@app.route('/deletedoc', methods = ['POST'])
def deletedoc():
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM admin WHERE Username = %s', [session['username']])
    account = cursor.fetchone()
    if request.method == 'POST' and request.form['delete']:

        cur = mysql.get_db().cursor()
        cur.execute("SELECT * FROM doctors")
        data = cur.fetchall()
        cursor.execute("DELETE FROM doctors where ID = %s", (session['delete']))
        flash('A doctor has been deleted')

        session.pop('delete', None)

        return redirect(url_for('viewdoctor'))
    else:
        return redirect(url_for('viewdoctor'))

#Update personal profile
@app.route('/updatemy/<int:ID>/')
def updatemy(ID):
    #data = db.read(ID)
    cur = mysql.get_db().cursor()
    cur.execute("SELECT * FROM users WHERE ID=%s", [ID])
    data = cur.fetchall()
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM admin WHERE Username = %s', [session['username']])
    account = cursor.fetchone()

    if len(data) == 0:
        return redirect(url_for('view', data = data,account=account))
    else:
        session['update'] = ID
        return render_template('updatemy.html', data = data,account=account)

@app.route('/updateusermy', methods = ['POST'])
def updateusermy():
    cur = mysql.get_db().cursor()
    cur.execute('SELECT * FROM users')
    data = cur.fetchall()
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM admin WHERE Username = %s', [session['username']])
    account = cursor.fetchone()
    if request.method == 'POST' and request.form['update']:
        cursor.execute("UPDATE users set Username = %s, Email = %s, Full_Name= %s, Address= %s, Blood_Group=%s, Age = %s where ID = %s",
                           (request.form['Username'], request.form['Email'],request.form['Full_Name'],request.form['Address'],request.form['Blood_Group'],request.form['date'],session['update']))

        flash('A user has been updated')

        session.pop('update', None)

        return redirect(url_for('myaccount', data = data,account=account))
    else:
        return redirect(url_for('myaccount', data = data,account=account))

# forgot User password
@app.route('/userpasforgot', methods = ['POST','GET'])
def userpasforgot():
    if 'loggedin' in session:
        return redirect('/')
    if request.method == "POST":
        email = request.form["email"]
        token = str(uuid.uuid4())
        cur = mysql.get_db().cursor()
        result = cur.execute("SELECT * FROM users Where email=%s",[email])
        if result>0:
            data = cur.fetchone()
            msg = Message(subject="Forgot password request ", sender="chalielijalem@gmail.com", recipients=[email])
            msg.body = render_template("sent.html", token=token, data=data)
            mail.send(msg)
            cur = mysql.get_db().cursor()
            cur.execute("UPDATE users SET token=%s Where email=%s",[token,email])
            mysql.get_db().commit()
            cur.close()
            flash("Email already sent to your email", "success")
            return redirect('/userpasforgot')
        else:
            flash("Email do not match","danger")

    return render_template('userforgot.html')

# reset User password
@app.route('/userpassreset/<token>', methods = ['POST','GET'])
def userpassreset(token):
    if 'loggedin' in session:
        return redirect('/')
    if request.method == "POST":
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        token1 = str(uuid.uuid4())
        if password != confirm_password:
            flash("Password donot match", "danger")
            return redirect("userpassreset")
        password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cur = mysql.get_db().cursor()
        m=cur.execute("SELECT * FROM users Where token=%s",[token])
        user = cur.fetchone()
        if m>0:
            cur = mysql.get_db().cursor()
            cur.execute("UPDATE users SET token=%s, password=%s WHERE token=%s",[token1, password, token])
            mysql.get_db().commit()
            cur.close()
            flash("Your password successfully updated","success")
            return redirect("/login")
        else:
            flash("Your Token is invalid", "danger")
            return redirect('/')
    return render_template('userreset.html')

 # Contact Us storing messages to database
@app.route("/contact",methods=["Post"])
def contact():
    # Getting data from inout fields and storing them in these variables
    if request.method == "POST":
        name= request.form["name"]
        email=request.form['email']
        phone=request.form['phone']
        message=request.form['message']
        cur = mysql.get_db().cursor()
        cur.execute('INSERT INTO ContactUs VALUES (%s, %s, %s,%s)', (name, email, phone, message))
        mysql.get_db().commit()
        cur.close()
        flash("Your message successfully sent","success")
        return redirect("/#contact")
    return render_template('index.html')       

# http://localhost:5000/logout - this will be the logout page
@app.route('/logout')
def logout():
   # Remove session data, this will log the user out
   cur = mysql.get_db().cursor()
   x = '0'
   uid=session['id']
   if(session['isdoctor']==0):
       cur.execute("UPDATE users SET online=%s WHERE id=%s", (x, uid))
   else:
       cur.execute("UPDATE doctors SET online=%s WHERE id=%s", (x, uid))
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   session.clear()
   # Redirect to login page
   return redirect(url_for('index'))

#run the Flask Server
if __name__ == '__main__':
    socketio.run(app)
#"""-------------------------------End of Web Application-------------------------------"""
