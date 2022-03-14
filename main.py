from __future__ import unicode_literals
from __future__ import print_function
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash,abort
from flaskext.mysql import MySQL
from pip import main
from datetime import datetime
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
import nltk
import pybase64


app = Flask(__name__)

port = int(os.environ.get('PORT', 5000))


# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'canada$God7972#'

# Enter your database connection details below
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD	'] = ''
app.config['MYSQL_DATABASE_DB'] = 'pharmacat'

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
        else:
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM doctors WHERE ID = %s', [session['id']])
        account = cursor.fetchone()
        cursor1 = mysql.get_db().cursor()
        records = cursor.execute('SELECT * FROM users')
        return render_template('dashboard.html', account = account, num = records,isdoctor=session['isdoctor'])
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
            session['api'] = account[8]
            session['isdoctor'] = 0
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
        age = request.form['age']
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
            cursor.execute('INSERT INTO users VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s)', (username, hashed_password, email, full_name, address, blood, age, api))
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
            cursor.execute('INSERT INTO doctors VALUES (NULL, %s, %s, %s, %s, %s, %s ,%s, %s, %s)', ( username, hashed_password, email, full_name, registration_number, contact_number, "" , spec, address ))
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
            session['isdoctor'] = 1
            # Redirect to home page
            return doc_dash()
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    flash(msg)
    return render_template('doctorlogin.html', msg=msg)

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
        return render_template('healthstatus.html', account=account)
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
                    print("\n\n")
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
        API_KEY = 'Enter your key'
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



"""
Code for the Chat App
which is based on Sockets.io
"""

socketio = SocketIO(app)

#Main Chat Interface
@app.route('/chat')
def sessions():
    return render_template('chat.html')

#Log Success of Messages
def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

#Handles sending and receiving of Messages
@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    socketio.emit('my response', json, callback=messageReceived)


# http://localhost:5000/logout - this will be the logout page
@app.route('/logout')
def logout():
   # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))




#appointment for personal user
#@app.route('/')
##def index():
#    return render_template('home.html')

@app.route('/instruction')
def instruction():
    return render_template('instruction.html')

#@app.route('/doctors')
#def doctor():
#    return render_template('doctors.html', doctors = doc)

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=4, max=50)])
    doc_id = StringField('Doc_id', [validators.Length(min=1, max=50)])
    address = StringField('Address', [validators.Length(min=5, max=50)])
    address2 = StringField('Address2', [validators.Length(min=5, max=50)])


@app.route('/cudoc', methods=['GET', 'POST'])
def cudoc():
    cur = mysql.get_db().cursor()

    result = cur.execute("SELECT * FROM docinfo")
    docinfo = cur.fetchall()

    if result > 0:
        return render_template('cudoc.html', docinfo=docinfo)
    else:
        msg = 'No Doctor Information'
        return render_template('cudoc.html', msg=msg)
    cur.close()

#Delete doctor info
@app.route('/delete_docinfo/<string:id>', methods=['POST'])
def delete_docinfo(id):
    #create cursor
    cur = mysql.get_db().cursor()
    cur.execute("DELETE FROM docinfo WHERE docid = %s", [id])
    cur.execute("DELETE FROM avapp WHERE docid = %s", [id])
    cur.execute("DELETE FROM boapp WHERE docid = %s", [id])
    cur.execute("DELETE FROM unavapp WHERE docid = %s", [id])
    mysql.get_db().commit()
    cur.close()

    flash('Doctor Deleted', 'success')
    return redirect(url_for('cudoc'))



@app.route('/input', methods=['GET', 'POST'])
def input():
    msg=''
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        doc_id = form.doc_id.data
        doc_id1 = int(doc_id) + 1
        address = form.address.data
        address2 = form.address2.data

        #create cursor
        cur = mysql.get_db().cursor()
        #execute
        cur.execute("INSERT INTO docinfo(name, docid, address, address2) VALUES(%s, %s, %s, %s)", (name, doc_id, address, address2))

        #create availabe appointment
        cur.execute("INSERT INTO avapp(name, docid, address, dateid, date) VALUES(%s, %s, %s, %s, 'MON morning')", (name, doc_id, address, int(doc_id) + 2))
        cur.execute("INSERT INTO avapp(name, docid, address, dateid, date) VALUES(%s, %s, %s, %s, 'MON morning')", (name, doc_id, address2, int(doc_id) + 2))

        cur.execute("INSERT INTO avapp(name, docid, address, dateid, date) VALUES(%s, %s, %s, %s, 'MON afternoon')", (name, doc_id, address, int(doc_id) + 4))
        cur.execute("INSERT INTO avapp(name, docid, address, dateid, date) VALUES(%s, %s, %s, %s, 'MON afternoon')", (name, doc_id, address2, int(doc_id) + 4))

        cur.execute("INSERT INTO avapp(name, docid, address, dateid, date) VALUES(%s, %s, %s, %s, 'TUE morning')", (name, doc_id, address, int(doc_id) + 6))
        cur.execute("INSERT INTO avapp(name, docid, address, dateid, date) VALUES(%s, %s, %s, %s, 'TUE morning')", (name, doc_id, address2, int(doc_id) + 6))

        cur.execute("INSERT INTO avapp(name, docid, address, dateid, date) VALUES(%s, %s, %s, %s, 'TUE afternoon')", (name, doc_id, address, int(doc_id) + 8))
        cur.execute("INSERT INTO avapp(name, docid, address, dateid, date) VALUES(%s, %s, %s, %s, 'TUE afternoon')", (name, doc_id, address2, int(doc_id) + 8))

        cur.execute("INSERT INTO avapp(name, docid, address, dateid, date) VALUES(%s, %s, %s, %s, 'WED morning')", (name, doc_id, address, int(doc_id) + 10))
        cur.execute("INSERT INTO avapp(name, docid, address, dateid, date) VALUES(%s, %s, %s, %s, 'WED morning')", (name, doc_id, address2, int(doc_id) + 10))

        cur.execute("INSERT INTO avapp(name, docid, address, dateid, date) VALUES(%s, %s, %s, %s, 'WED afternoon')", (name, doc_id, address, int(doc_id) + 12))
        cur.execute("INSERT INTO avapp(name, docid, address, dateid, date) VALUES(%s, %s, %s, %s, 'WED afternoon')", (name, doc_id, address2, int(doc_id) + 12))

        cur.execute("INSERT INTO avapp(name, docid, address, dateid, date) VALUES(%s, %s, %s, %s, 'THR morning')", (name, doc_id, address, int(doc_id) + 14))
        cur.execute("INSERT INTO avapp(name, docid, address, dateid, date) VALUES(%s, %s, %s, %s, 'THR morning')", (name, doc_id, address2, int(doc_id) + 14))

        cur.execute("INSERT INTO avapp(name, docid, address, dateid, date) VALUES(%s, %s, %s, %s, 'THR afternoon')", (name, doc_id, address, int(doc_id) + 16))
        cur.execute("INSERT INTO avapp(name, docid, address, dateid, date) VALUES(%s, %s, %s, %s, 'THR afternoon')", (name, doc_id, address2, int(doc_id) + 16))

        cur.execute("INSERT INTO avapp(name, docid, address, dateid, date) VALUES(%s, %s, %s, %s, 'FRI morning')", (name, doc_id, address, int(doc_id) + 18))
        cur.execute("INSERT INTO avapp(name, docid, address, dateid, date) VALUES(%s, %s, %s, %s, 'FRI morning')", (name, doc_id, address2, int(doc_id) + 18))

        cur.execute("INSERT INTO avapp(name, docid, address, dateid, date) VALUES(%s, %s, %s, %s, 'FRI afternoon')", (name, doc_id, address, int(doc_id) + 20))
        cur.execute("INSERT INTO avapp(name, docid, address, dateid, date) VALUES(%s, %s, %s, %s, 'FRI afternoon')", (name, doc_id, address2, int(doc_id) + 20))

        #commit to DB
        mysql.get_db().commit()
        cur.close()
        msg='Input successful', 'success'
        flash(msg)
        return render_template('instruction.html')
        #redirect(url_for('instruction'))
    return render_template('input.html', form=form)


@app.route('/makeapp', methods=['GET', 'POST'])
def makeapp():
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
                arr.append([doc[1],doc[9]])
                
            return render_template('appointments.html', account=account,l=l,arr=arr)
        # User is not loggedin redirect to login page
        

 #       cur = mysql.get_db().cursor()

  #      result = cur.execute("SELECT * FROM doctors")
  #      appinfo = cur.fetchall()

  #      if result > 0:
  #          return render_template('appointments.html', appinfo=appinfo)
  #      else:
  #          msg = 'No Available Appointment'
   #         return render_template('appointments.html', msg=msg)
   #     cur.close()
    return redirect(url_for('login'))

@app.route('/book_app/<string:id>', methods=['POST'])
def book_app(id):
    #create cursor
    cur = mysql.get_db().cursor()
    resultaa = cur.execute("SELECT dateid FROM avapp WHERE id = %s", [id])
    aaaa = cur.fetchall()
    #print ('%s', aaaa[0][1])
    cur.execute("INSERT INTO booking(name, docid, dateid, date, address) SELECT Full_Name, ID, Specialization, Username, Address FROM doctors WHERE ID = %s", [id] )
    #cur.execute("DELETE FROM avapp WHERE id = %s", [id])
    cur.execute("INSERT INTO unavapp(name, docid, dateid, date, address) SELECT Full_Name, ID, Specialization, Username, Address FROM doctors WHERE id = %s", [id] )
    #cur.execute("DELETE FROM avapp WHERE dateid = %s", aaaa[0][0])
    # cur.execute("DELETE FROM avapp WHERE id = %s", [id])
    mysql.get_db().commit()
    cur.close()
    flash('Appointment is made', 'success')
    return redirect(url_for('makeapp'))


@app.route('/curapp', methods=['GET', 'POST'])
def curapp():
    cur = mysql.get_db().cursor()
    result = cur.execute("SELECT * FROM boapp")
    appinfo = cur.fetchall()

    if result > 0:
        return render_template('curapp.html', appinfo=appinfo)
    else:
        msg = 'No Current Appointment'
        return render_template('curapp.html', msg=msg)
    cur.close()


@app.route('/cancel_app/<string:id>', methods=['POST'])
def cancel_app(id):
    #create cursor
    cur = mysql.get_db().cursor()
    resultbb = cur.execute("SELECT dateid FROM boapp WHERE id = %s", [id])
    bbbb = cur.fetchall()
    cur.execute("INSERT INTO avapp(name, docid, dateid, date, address) SELECT name, docid, dateid, date, address FROM boapp WHERE id = %s", [id] )
    cur.execute("DELETE FROM boapp WHERE id = %s", [id])
    cur.execute("INSERT INTO avapp(name, docid, dateid, date, address) SELECT name, docid, dateid, date, address FROM unavapp WHERE dateid = '%s'", bbbb[0][0] )
    cur.execute("DELETE FROM unavapp WHERE dateid = %s", bbbb[0][0])
    mysql.get_db().commit()
    cur.close()
    flash('Appointment is canceled', 'success')
    return redirect(url_for('curapp'))





#run the Flask Server
if __name__ == '__main__':
    app.run(debug=True)
#"""-------------------------------End of Web Application-------------------------------"""
