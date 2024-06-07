import os
from posixpath import dirname, join
import re
from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, flash, jsonify, render_template, request, redirect, session, url_for
from pymongo import MongoClient
import bcrypt
from werkzeug.utils import secure_filename

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  str(os.environ.get("DB_NAME"))

# Configuration for file uploads
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

users_collection = db['users']
products_collection = db["products"]
pemesanan_collection = db["pemesanan"]
pembayaran_collection = db["pembayaran"]
produkTerlaris_collection = db["produkTerlaris"]
bannerHomepage_collection = db["bannerHomepage"]
riwayatPemesanan_collection = db["riwayatPemesanan"]
admin_collection = db["admin"]
footer_collection = db["footer"]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
                return redirect(url_for('index'))
            else:
                flash("Email atau Password salah")
                return redirect(url_for('login_user'))
        else:
            flash("Gagal, User tidak ditemukan")
            return redirect(url_for('login_user'))
    else:
        return render_template('loginUser.html')
    
@app.route('/produk', methods=['GET'])
def produk():
    products = products_collection.find()
    return render_template('produk.html', products=products)

@app.route('/sidebar')
def sidebar():
    return render_template('sidebarAdmin.html')

@app.route('/adminDashboard')
def adminDashboard():
    return render_template('adminDashboard.html')

@app.route('/adminProduk')
def adminProduk():
    products = products_collection.find()
    return render_template('adminProduk.html', products=products)

@app.route('/add_product', methods=['POST'])
def add_product():
    if 'photo' not in request.files:
        return jsonify({"status": "error", "message": "No file part"})
    
    file = request.files['photo']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        data = request.form
        jenis_skincare = data['jenisSkincare']
        nama_produk = data['namaProduk']
        harga_per_pcs = data['hargaPerPcs']
        total_dus = data['totalDus']
        total_harga = data['totalHarga']

        product = {
            "jenis_skincare": jenis_skincare,
            "nama_produk": nama_produk,
            "harga_per_pcs": harga_per_pcs,
            "total_dus": total_dus,
            "total_harga": total_harga,
            "photo": filename
        }

        products_collection.insert_one(product)
        return jsonify({"status": "success", "message": "Product added successfully!"})
    else:
        return jsonify({"status": "error", "message": "Invalid file type"})
    
@app.route('/edit_product', methods=['POST'])
def edit_product():
    data = request.form
    product_id = data['productId']
    jenis_skincare = data['editJenisSkincare']
    nama_produk = data['editNamaProduk']
    harga_per_pcs = data['editHargaPerPcs']
    total_dus = data['editTotalDus']
    total_harga = data['editTotalHarga']

    # Lakukan pembaruan data pada database sesuai dengan product_id
    products_collection.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {
            "jenis_skincare": jenis_skincare,
            "nama_produk": nama_produk,
            "harga_per_pcs": harga_per_pcs,
            "total_dus": total_dus,
            "total_harga": total_harga
        }}
    )

    return jsonify({"status": "success", "message": "Product updated successfully!"})

@app.route('/hapusDataProduk/<string:_id>', methods=["GET", "POST"])
def hapus_data_produk(_id):
    db.products.delete_one({'_id': ObjectId(_id)})
    return redirect(url_for('admin_produk'))

@app.route('/adminPelanggan')
def adminPelanggan():
    users = users_collection.find()
    return render_template('adminPelanggan.html', users=users)

@app.route('/hapusDataPelanggan/<string:_id>', methods=["GET", "POST"])
def hapus_data_pelanggan(_id):
    db.users.delete_one({'_id': ObjectId(_id)})
    return redirect(url_for('admin_pelanggan'))

@app.route('/adminPemesanan')
def adminPemesanan():
    return render_template('adminPemesanan.html')

@app.route('/adminPembayaran')
def adminPembayaran():
    pembayaran = db.pembayaran.find()
    return render_template('adminPembayaran.html', pembayaran=pembayaran)

@app.route('/addPembayaran', methods=['POST'])
def add_pembayaran():
    data = {
        'metodePembayaran': request.form.get['metodePembayaran'],
        'jenisPembayaran': request.form.get['jenisPembayaran'],
        'nomorPembayaran': request.form.get['nomorPembayaran']
    }
    db.pembayaran.insert_one(data)
    return jsonify({'status': 'Data berhasil ditambahkan'})

@app.route('/hapusDataPembayaran/<id>', methods=['POST'])
def hapus_data_pembayaran(id):
    db.pembayaran.delete_one({'_id': ObjectId(id)})
    return jsonify({'status': 'Data berhasil dihapus'})

@app.route('/adminProdukTerlaris')
def adminProdukTerlaris():
    return render_template('adminProdukTerlaris.html')

@app.route('/adminBannerHomepage')
def adminBannerHomepage():
    return render_template('adminBannerHomepage.html')

@app.route('/adminFooter')
def adminFooter():
    return render_template('adminFooter.html')

@app.route('/adminDataAdmin')
def adminDataAdmin():
    return render_template('adminDataAdmin.html')

@app.route('/adminRiwayatPemesanan')
def adminRiwayatPemesanan():
    return render_template('adminRiwayatPemesanan.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=8000, host="0.0.0.0")
    