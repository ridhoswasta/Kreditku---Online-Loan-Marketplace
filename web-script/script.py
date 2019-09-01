#importing libraries
import os
import numpy as np
import flask
import pickle
from flask import Flask, render_template, request,  redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from flask import jsonify
from werkzeug.utils import secure_filename


#creating instance of the class
app=Flask(__name__)
app.secret_key = 'Karenaallah1'
UPLOAD_FOLDER = 'static/fotokreditur'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'remotemysql.com'
app.config['MYSQL_USER'] = 'GxIIyrWVuB'
app.config['MYSQL_PASSWORD'] = '5TZ2S3YBDm'
app.config['MYSQL_DB'] = 'GxIIyrWVuB'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Intialize MySQL
mysql = MySQL(app)


#to tell flask what url shoud trigger the function index()
@app.route('/')

@app.route('/index/')
def index():
    return flask.render_template('index.html')


@app.route('/ajukanpinjaman/<id_kreditur>')
def ajukanpinjaman(id_kreditur):
    idkreditur = id_kreditur
    return flask.render_template('ajukanpinjaman.html', id_kreditur=idkreditur)

@app.route('/loginkreditur', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
          # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM akun WHERE username_pengguna = %s AND kata_sandi = %s', (username, password))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id_akun']
            session['username'] = account['username_pengguna']
            session['nama_pengguna'] = account['nama_pengguna']
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('loginkreditur.html', msg=msg)

# http://localhost:5000/python/logout - this will be the logout page
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))

# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/daftarkreditur', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        nama_pengguna = request.form['nama_pengguna']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

                # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM akun WHERE username_pengguna = %s', (username,))
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
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute("INSERT INTO akun VALUES (NULL, %s, %s, %s, %s, 1, 'Tidak ada ada deskripsi', 'nodata.png')", (nama_pengguna, username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('daftarkreditur.html', msg=msg)

# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for loggedin users
@app.route('/halamankreditur')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        cursor_diterima = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor_ditolak = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        id = session['id']
        print(id)
        cursor_diterima.execute('SELECT * FROM aplikasi_debitur WHERE id_akun = %s and status_aplikasi = 1', (id,))
        cursor_ditolak.execute('SELECT * FROM aplikasi_debitur WHERE id_akun = %s and status_aplikasi = 0', (id,))
        # Fetch one record and return result
#        daftar_aplikasi = cursor.fetchone()
#        nama_debitur = daftar_aplikasi['nama_debitur']
        data_diterima = cursor_diterima.fetchall()
        data_ditolak = cursor_ditolak.fetchall()
        mysql.connection.commit()
        # User is loggedin show them the home page
        return render_template('halamankreditur.html', username=session['nama_pengguna'], id=session['id'], data_diterima=data_diterima,data_ditolak=data_ditolak )
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/halamankreditur/updatedata', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        # check if the post request has the file part
        if 'file' not in request.files:
            msg = "No file part"
            return render_template('updatedata.html', msg=msg)
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            msg = 'No selected file'
            return render_template('updatedata.html', msg=msg)
        if file and file.filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS:
            filename = secure_filename(file.filename)
            id = session['id']
            username = session['username']
            deskripsi = request.form['Deskripsi']
            filename = username + filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename ))
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#            cursor.execute('INSERT INTO akun VALUES (NULL, %s, %s, %s, %s, 1)', (nama_pengguna, username, password, email,))
            cursor.execute('UPDATE akun SET deskripsi=%s,foto=%s WHERE id_akun = %s', (deskripsi, filename, id,))
            mysql.connection.commit()
            msg = "File Berhasil Diupload!"
            return render_template('updatedata.html', msg=msg)
    return render_template('updatedata.html')


@app.route('/daftarpinjaman')
def daftarpinjaman():
    cursor_daftarpinjaman = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor_daftarpinjaman.execute('SELECT * FROM akun')
    data_daftarpinjaman = cursor_daftarpinjaman.fetchall()
    return render_template('daftarpinjaman.html', data_daftarpinjaman=data_daftarpinjaman)

#prediction function
def ValuePredictor(to_predict_list):
    to_predict = np.array(to_predict_list).reshape(1,11)
#    to_predict = np.array(to_predict_list).reshape(1,11)
    #to_predict = to_predict[1:12]
    loaded_model = pickle.load(open("model_logreg.pkl","rb"))
    result = loaded_model.predict(to_predict)
    return result[0]

@app.route('/result',methods = ['GET', 'POST'])
def result():
    if request.method == 'POST':
        to_predict_list = request.form.to_dict()
        print(to_predict_list)
        to_predict_list=list(to_predict_list.values())
        data_sql = to_predict_list
        to_predict_list = to_predict_list[2:13]
        print(to_predict_list)
        to_predict_list = list(map(int, to_predict_list))
        result = ValuePredictor(to_predict_list)
        nama = request.form['Nama']
        gender = request.form['Gender']
        married = request.form['Married']
        dependents = request.form['Dependents']
        education = request.form['Education']
        self_Employed = request.form['Self_Employed']
        applicantIncome = request.form['ApplicantIncome']
        coapplicantIncome = request.form['CoapplicantIncome']
        loanamount = request.form['LoanAmount']
        loan_amount_term = request.form['Education']
        credit_history = request.form['Credit_History']
        property_area = request.form['Property_Area']
        id_akun = request.form['id_akun']
        if result== 'Y':
            prediction='Selamat! Aplikasi anda untuk peminjaman diterima berdasarkan algoritma A.I kami.Aplikasi anda akan diteruskan kepada kreditur untuk proses lebih lanjut. '
            print(to_predict_list)
            status_aplikasi=1
            color ='green';
        else:
            prediction='Mohon maaf aplikasi anda dinyatakan ditolak berdasarkan algoritma A.I kami.Namun jangan berkecil hati, kami akan tetap mengirimkan data kamu kepada kreditur untuk pertimbangan lebih lanjut.'
            print(to_predict_list)
            status_aplikasi=0
            color = 'red';
        #cursor.execute('INSERT INTO `kreditku`.`aplikasi_debitur` (`nama_debitur`, `jenis_kelamin`, `status_pernikahan`, `jumlah_tanggungan`, `pendidikan_terakhir`, `usaha_sendiri`, `pemasukan`, `pemasukan_pasangan`, `jumlah_pinjaman`, `jangka_waktu`, `pernah_meminjam`, `tempat_tinggal`, `id_akun`, `status_aplikasi`) VALUES ('ridho', '1', '1', '1', '1', '0', '1220', '1220', '2000', '360', '1', '3', '1', '1')', (nama_pengguna, username, password, email,))
        #mysql.connection.commit()
        print(id_akun)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO aplikasi_debitur VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (nama, gender, married, dependents, education,self_Employed, applicantIncome, coapplicantIncome, loanamount, loan_amount_term, credit_history, property_area, id_akun, status_aplikasi,))
        mysql.connection.commit()
        #cursor.execute('(NULL, test')
        return render_template("result.html",prediction=prediction, nama=nama, loanamount=loanamount, color=color)
