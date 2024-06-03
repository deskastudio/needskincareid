import os
from posixpath import dirname, join
import re
from dotenv import load_dotenv
from flask import Flask, flash, render_template, request, redirect, session, url_for
from pymongo import MongoClient
import bcrypt

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  str(os.environ.get("DB_NAME"))

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

users_collection = db['users']

app = Flask(__name__)

app.secret_key = os.urandom(24)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registerUser', methods=['POST', 'GET'])
def register_user():
    if request.method == 'GET':
        return render_template('registerUser.html')
    else:
        namaLengkap = request.form['nama-lengkap']
        namaPengguna = request.form['nama-pengguna']
        email = request.form['email']
        password1 = request.form['password1'].encode('utf-8')
        password2 = request.form['password2'].encode('utf-8')
        hash_password = bcrypt.hashpw(password1, bcrypt.gensalt())
        
        if not namaLengkap or not namaPengguna or not email or not password1 or not password2:
            flash('Tolong isi semua form yang tersedia')
            return redirect(url_for('register_user'))
        
        if len(password1) < 8:
            flash('password minimal 8 karakter')
            return redirect(url_for('register_user'))
        
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('Invalid email address')
            return redirect(url_for('register_user'))

        if password1 != password2:
            flash('Passwords do not match')
            return redirect(url_for('register_user'))

        if users_collection.find_one({'email': email}): 
            flash('Email already exists')
            return redirect(url_for('register_user'))
        
        new_user = {
            'namaLengkap': namaLengkap,
            'namaPengguna': namaPengguna,
            'email': email,
            'password': hash_password
        }

        user_id = users_collection.insert_one(new_user).inserted_id
        session['user_id'] = str(user_id)
        session['email'] = email
        session['namaLengkap'] = namaLengkap
        session['namaPengguna'] = namaPengguna
        return redirect(url_for('login_user'))

@app.route('/loginUser', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        namaPengguna = request.form['nama-pengguna']
        password = request.form['password']

        user = users_collection.find_one({'namaPengguna': namaPengguna})

        if user is not None:
            if bcrypt.checkpw(password.encode('utf-8'), user['password']):
                session['nama-lengkap'] = user['namaLengkap']
                session['email'] = user['email']
                session['user_id'] = str(user['_id'])
                return redirect(url_for('produk'))
            else:
                flash("Email atau Password salah")
                return redirect(url_for('login_user'))
        else:
            flash("Gagal, User tidak ditemukan")
            return redirect(url_for('login_user'))
    else:
        return render_template('loginUser.html')
    
@app.route('/produk')
def produk():
    return render_template('produk.html')

@app.route('/sidebar')
def sidebar():
    return render_template('sidebarAdmin.html')


if __name__ == '__main__':
    app.run(debug=True, port=8000, host="0.0.0.0")
    