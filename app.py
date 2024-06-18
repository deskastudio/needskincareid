from functools import wraps
from io import BytesIO
import os
from posixpath import dirname, join
import re
from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, flash, jsonify, make_response, render_template, request, redirect, session, url_for
from pymongo import DESCENDING, MongoClient
import bcrypt
import pymongo
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  str(os.environ.get("DB_NAME"))

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

users_collection = db['users']

app = Flask(__name__)
app.secret_key = os.urandom(24)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Anda harus masuk untuk mengakses halaman ini.')
            return redirect(url_for('login_user'))
        return f(*args, **kwargs)
    return decorated_function

def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Anda harus masuk untuk mengakses halaman ini.')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    try:
        bannerHomepage = list(db.bannerHomepage.find({}))
        pembayaran = list(db.pembayaran.find({}))
        products = list(db.products.find({'showOnHomepage': True}))
        return render_template('index.html', products=products, pembayaran=pembayaran, bannerHomepage=bannerHomepage)
    except Exception as e:
        return str(e)

@app.route('/updateShowOnHomepageStatus/<product_id>', methods=['POST'])
def update_show_on_homepage_status(product_id):
    try:
        show_on_homepage = request.json.get('showOnHomepage')
        # Update status checkbox di MongoDB
        db.products.update_one(
            {'_id': ObjectId(product_id)},
            {'$set': {'showOnHomepage': show_on_homepage}}
        )
        return jsonify({'message': 'Status updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
            flash('Alamat email tidak valid')
            return redirect(url_for('register_user'))

        if password1 != password2:
            flash('Kata sandi tidak cocok')
            return redirect(url_for('register_user'))

        if users_collection.find_one({'email': email}): 
            flash('Email sudah ada')
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
    
@app.route('/adminLogin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        namaPengguna = request.form['namaPengguna']
        password = request.form['password']

        admin = db.admin.find_one({'namaPengguna': namaPengguna})

        if admin and admin['password'] == password:
            session['admin_id'] = str(admin['_id'])
            return redirect(url_for('adminDashboard'))
        else:
            flash("Nama Pengguna atau Kata Sandi salah")
            return redirect(url_for('admin_login'))

    return render_template('adminLogin.html')
    
@app.route('/produk', methods=['GET'])
def produk():
    products = db.products.find()
    return render_template('produk.html', products=products)

@app.route('/pemesanan', methods=['GET', 'POST'])
@login_required
def pemesanan():
    if request.method == 'POST':
        user_id = session.get('user_id')  # Dapatkan user_id dari sesi
        product_id = request.form.get('product_id')
        nama_lengkap = request.form.get('namaLengkap')
        nomor_telepon = request.form.get('nomorTelepon')
        jumlah_produk = request.form.get('jumlahProduk')
        alamat = request.form.get('alamat')
        tanggal_pemesanan = request.form.get('tanggalPemesanan')

        # Ambil nama produk dan foto produk dari sesi
        nama_produk = session.get('nama_produk')
        foto_produk = session.get('foto_produk')

        # Simpan data pemesanan ke basis data
        new_order = {
            'user_id': ObjectId(user_id),  # Tambahkan user_id ke data pemesanan
            'product_id': ObjectId(product_id),
            'nama_produk': nama_produk,
            'foto_produk': foto_produk,
            'nama_lengkap': nama_lengkap,
            'nomor_telepon': nomor_telepon,
            'jumlah_produk': jumlah_produk,
            'alamat': alamat,
            'tanggal_pemesanan': tanggal_pemesanan
        }
        db.orders.insert_one(new_order)

        # Redirect ke halaman detail pemesanan dengan menyertakan ID pemesanan
        return redirect(url_for('detail_pemesanan', id=new_order['_id']))

    else:
        product_id = request.args.get('id')
        product = db.products.find_one({'_id': ObjectId(product_id)})
        if product:
            # Simpan nama produk dan foto produk dalam sesi
            session['nama_produk'] = product['nama_produk']
            session['foto_produk'] = product.get('photo', 'default.png')  # Gunakan 'default.png' jika tidak ada foto
            return render_template('pemesanan.html', product=product)
        else:
            return "Produk tidak ditemukan."



@app.route('/detailPemesanan/<id>')
@login_required
def detail_pemesanan(id):
    pembayaran = db.pembayaran.find()
    order = db.orders.find_one({'_id': ObjectId(id)})
    if order:
        product_id = order['product_id']
        product = db.products.find_one({'_id': product_id}) 
        if product:
            return render_template('detailPemesanan.html', order=order, product=product, pembayaran=pembayaran)
        else:
            return "Produk tidak ditemukan."
    else:
        return "Pemesanan tidak ditemukan."
    
@app.route('/totals', methods=['GET'])
@admin_login_required
def get_totals():
    total_customers = db.users.count_documents({})
    total_products = db.products.count_documents({})
    total_orders = db.orders.count_documents({})
    
    return jsonify({
        'total_customers': total_customers,
        'total_products': total_products,
        'total_orders': total_orders
    })



# route admin dashboard start
@app.route('/adminDashboard')
@admin_login_required
def adminDashboard():
    admin = db.admin.find_one({'_id': ObjectId(session.get('admin_id'))})
    return render_template('adminDashboard.html', admin=admin)
# route admin dashboard end



# route admin produk start
@app.route('/adminProduk')
@admin_login_required
def adminProduk():
    admin = db.admin.find_one({'_id': ObjectId(session.get('admin_id'))})
    products = db.products.find()
    return render_template('adminProduk.html', products=products, admin=admin)


@app.route('/tambahDataProduk', methods=['GET', 'POST'])
@admin_login_required
def tambah_data_produk():
    if request.method == 'POST':
        jenisSkincare = request.form['jenisSkincare']
        namaProduk = request.form['namaProduk']
        hargaPerPcs = request.form.getlist('hargaPerPcs[]')
        totalDus = request.form.getlist('totalDus[]')
        totalHarga = request.form.getlist('totalHarga[]')
        photo = request.files['photo']

        # Validasi input
        if not jenisSkincare or not namaProduk or not hargaPerPcs or not totalDus or not totalHarga or not photo:
            return "Semua bidang harus diisi!", 400

        if photo:
            nama_file_asli = photo.filename
            nama_file_gambar = secure_filename(nama_file_asli)
            file_path = f'./static/assets/imgProduk/{nama_file_gambar}'
            photo.save(file_path)
        else:
            nama_file_gambar = None

        # Buat daftar entri total dus dan total harga
        dus_harga_list = []
        for harga_pcs, dus, harga in zip(hargaPerPcs, totalDus, totalHarga):
            dus_harga_list.append({'hargaPerPcs': harga_pcs, 'total_dus': dus, 'total_harga': harga})

        # Buat dokumen untuk disimpan di database
        doc = {
            'jenis_skincare': jenisSkincare,
            'nama_produk': namaProduk,
            'dus_harga': dus_harga_list,
            'photo': nama_file_gambar
        }

        # Simpan dokumen ke MongoDB
        db.products.insert_one(doc)
        return redirect(url_for("adminProduk"))

    return render_template('tambahDataProduk.html')

@app.route('/editDataProduk/<string:_id>', methods=["GET", "POST"])
@admin_login_required
def edit_data_produk(_id):
    admin = db.admin.find_one({'_id': ObjectId(session.get('admin_id'))})
    if request.method == 'POST':
        jenisSkincare = request.form['jenisSkincare']
        namaProduk = request.form['namaProduk']
        hargaPerPcs = request.form.getlist('hargaPerPcs[]')
        totalDus = request.form.getlist('totalDus[]')
        totalHarga = request.form.getlist('totalHarga[]')
        photo = request.files.get('photo')  # Menggunakan get() agar tidak error jika tidak ada foto yang diunggah

        # Inisialisasi nama_file_gambar dengan nilai default
        nama_file_gambar = None

        # Simpan file jika ada
        if photo and photo.filename:  # Periksa jika ada foto yang diunggah
            nama_file_asli = photo.filename
            nama_file_gambar = secure_filename(nama_file_asli)
            file_path = f'./static/assets/imgProduk/{nama_file_gambar}'
            photo.save(file_path)
        
        # Buat dictionary untuk update
        doc = {
            'jenis_skincare': jenisSkincare,
            'nama_produk': namaProduk,
            'dus_harga': [{'hargaPerPcs': harga_pcs, 'total_dus': dus, 'total_harga': harga} for harga_pcs, dus, harga in zip(hargaPerPcs, totalDus, totalHarga)]
        }

        # Tambahkan nama_file_gambar ke dictionary jika ada
        if nama_file_gambar:
            doc['photo'] = nama_file_gambar
        
        # Update database
        db.products.update_one({'_id': ObjectId(_id)}, {'$set': doc})
        return redirect(url_for('adminProduk'))
    
    data = db.products.find_one({'_id': ObjectId(_id)})
    return render_template('editDataProduk.html', data=data, admin=admin)


@app.route('/hapusDataProduk/<string:_id>', methods=["GET", "POST"])
@admin_login_required
def hapus_data_produk(_id):
    db.products.delete_one({'_id': ObjectId(_id)})
    return redirect(url_for('adminProduk'))

# route admin produk end



# route admin pelanggan start
@app.route('/adminPelanggan', methods=['GET'])
@admin_login_required
def adminPelanggan():
    admin = db.admin.find_one({'_id': ObjectId(session.get('admin_id'))})
    users = db.users.find()
    page = int(request.args.get('page', 1))
    per_page = 5  # Number of users per page
    total_users = users_collection.count_documents({})
    total_pages = (total_users + per_page - 1) // per_page

    users = list(users_collection.find().skip((page - 1) * per_page).limit(per_page))

    return render_template('adminPelanggan.html', users=users, page=page, total_pages=total_pages, admin=admin)
    

@app.route('/hapusDataPelanggan/<string:_id>', methods=["GET", "POST"])
@admin_login_required
def hapus_data_pelanggan(_id):
    db.users.delete_one({'_id': ObjectId(_id)})
    return redirect(url_for('adminPelanggan'))
# route admin pelanggan end



# route admin pemesanan start
@app.route('/adminPemesanan')
@admin_login_required
def adminPemesanan():
    admin = db.admin.find_one({'_id': ObjectId(session.get('admin_id'))})
    orders = db.orders.find()
    page = int(request.args.get('page', 1))
    per_page = 5
    total_products = db.orders.count_documents({})
    total_pages = (total_products + per_page - 1) // per_page

    orders = list(db.orders.find().sort('_id', pymongo.DESCENDING).skip((page - 1) * per_page).limit(per_page))

    return render_template('adminPemesanan.html', orders=orders, page=page, total_pages=total_pages, admin=admin)
# route admin pemesanan end

@app.route('/selesaikan-pesanan/<string:_id>', methods=['POST'])
@admin_login_required
def selesaikan_pemesanan(_id):
    try:
        orders = db.orders.find_one_and_delete({"_id": ObjectId(_id)})
        if orders:
            db.riwayatPemesanan.insert_one(orders)
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "error": "Pesanan tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# route admin pembayaran start
@app.route('/adminPembayaran', methods=['GET'])
@admin_login_required
def adminPembayaran():
        admin = db.admin.find_one({'_id': ObjectId(session.get('admin_id'))})
        pembayaran = db.pembayaran.find()
        page = int(request.args.get('page', 1))
        per_page = 5  # Number of products per page
        total_products = db.pembayaran.count_documents({})
        total_pages = (total_products + per_page - 1) // per_page

        pembayaran = list(db.pembayaran.find().skip((page - 1) * per_page).limit(per_page))

        return render_template('adminPembayaran.html', pembayaran=pembayaran, page=page, total_pages=total_pages, admin=admin)

@app.route('/tambahDataPembayaran', methods=['GET', 'POST'])
@admin_login_required
def tambah_data_pembayaran():
    admin = db.admin.find_one({'_id': ObjectId(session.get('admin_id'))})
    if request.method == 'POST':
        jenisPembayaran = request.form['jenisPembayaran']
        metodePembayaran = request.form['metodePembayaran']
        nomorPembayaran = request.form['nomorPembayaran']
            
        doc = {
            'jenisPembayaran': jenisPembayaran,
            'metodePembayaran': metodePembayaran,
            'nomorPembayaran': nomorPembayaran
        }
        
        db.pembayaran.insert_one(doc)
        return redirect(url_for("adminPembayaran"))
        
    return render_template('tambahDataPembayaran.html', admin=admin)

@app.route('/editDataPembayaran/<string:_id>', methods=["GET", "POST"])
@admin_login_required
def edit_data_pembayaran(_id):
    admin = db.admin.find_one({'_id': ObjectId(session.get('admin_id'))})
    if request.method == 'POST':
        jenisPembayaran = request.form['jenisPembayaran']
        metodePembayaran = request.form['metodePembayaran']
        nomorPembayaran = request.form['nomorPembayaran']
            
        doc = {
            'jenisPembayaran': jenisPembayaran,
            'metodePembayaran': metodePembayaran,
            'nomorPembayaran': nomorPembayaran
        }
        
        # Update database
        db.pembayaran.update_one({'_id': ObjectId(_id)}, {'$set': doc})
        return redirect(url_for('adminPembayaran'))
    
    data = db.pembayaran.find_one({'_id': ObjectId(_id)})
    return render_template('editDataPembayaran.html', data=data, admin=admin)


@app.route('/hapusDataPembayaran/<string:_id>', methods=["GET", "POST"])
@admin_login_required
def hapus_data_pembayaran(_id):
    db.pembayaran.delete_one({'_id': ObjectId(_id)})
    return redirect(url_for('adminPembayaran'))
# route admin pembayaran end



# route banner homepage start
@app.route('/adminBannerHomepage')
@admin_login_required
def adminBannerHomepage():
        admin = db.admin.find_one({'_id': ObjectId(session.get('admin_id'))})
        bannerHomepage = db.bannerHomepage.find()
        page = int(request.args.get('page', 1))
        per_page = 5  # Number of products per page
        total_banner = db.bannerHomepage.count_documents({})
        total_pages = (total_banner + per_page - 1) // per_page

        bannerHomepage = list(db.bannerHomepage.find().skip((page - 1) * per_page).limit(per_page))

        return render_template('adminBannerHomepage.html', bannerHomepage=bannerHomepage, page=page, total_pages=total_pages, admin=admin)

@app.route('/tambahDataBannerHomepage', methods=['GET', 'POST'])
@admin_login_required
def tambah_data_banner_homepage():
    admin = db.admin.find_one({'_id': ObjectId(session.get('admin_id'))})
    if request.method == 'POST':
        judulBanner = request.form['judulBanner']
        photo = request.files['photo']
        
        if photo:
            nama_file_asli = photo.filename
            nama_file_gambar = secure_filename(nama_file_asli)
            file_path = f'./static/assets/imgBannerHomepage/{nama_file_gambar}'
            photo.save(file_path)
        else:
            nama_file_gambar = None
            
        doc = {
            'judulBanner': judulBanner,
            'photo': nama_file_gambar
        }
        
        db.bannerHomepage.insert_one(doc)
        return redirect(url_for("adminBannerHomepage"))
        
    return render_template('tambahDataBannerHomepage.html', admin=admin)

@app.route('/editDataBannerHomepage/<string:_id>', methods=["GET", "POST"])
@admin_login_required
def edit_data_banner_homepage(_id):
    admin = db.admin.find_one({'_id': ObjectId(session.get('admin_id'))})
    if request.method == 'POST':
        judulBanner = request.form['judulBanner']
        photo = request.files['photo']

        # Inisialisasi nama_file_gambar dengan nilai default
        nama_file_gambar = None

        # Simpan file jika ada
        if photo:
            nama_file_asli = photo.filename
            nama_file_gambar = secure_filename(nama_file_asli)
            file_path = f'./static/assets/imgBannerHomepage/{nama_file_gambar}'
            photo.save(file_path)
        
        # Buat dictionary untuk update
        doc = {
            'judulBanner': judulBanner,
        }

        # Tambahkan nama_file_gambar ke dictionary jika ada
        if nama_file_gambar:
            doc['photo'] = nama_file_gambar
        
        # Update database
        db.bannerHomepage.update_one({'_id': ObjectId(_id)}, {'$set': doc})
        return redirect(url_for('adminBannerHomepage'))
    
    data = db.bannerHomepage.find_one({'_id': ObjectId(_id)})
    return render_template('editDataBannerHomepage.html', data=data, admin=admin)

@app.route('/hapusDataBannerHomepage/<string:_id>', methods=["GET", "POST"])
@admin_login_required
def hapus_data_banner_homepage(_id):
    db.bannerHomepage.delete_one({'_id': ObjectId(_id)})
    return redirect(url_for('adminBannerHomepage'))
# route produk terlaris end



# route data admin start
@app.route('/adminDataAdmin')
@admin_login_required
def adminDataAdmin():
        admin = db.admin.find_one({'_id': ObjectId(session.get('admin_id'))})
        admin = db.admin.find()
        page = int(request.args.get('page', 1))
        per_page = 5  # Number of products per page
        total_admin = db.admin.count_documents({})
        total_pages = (total_admin + per_page - 1) // per_page

        admin = list(db.admin.find().skip((page - 1) * per_page).limit(per_page))

        return render_template('adminDataAdmin.html', admin=admin, page=page, total_pages=total_pages)

@app.route('/tambahDataAdmin', methods=['GET', 'POST'])
@admin_login_required
def tambah_data_admin():
    admin = db.admin.find_one({'_id': ObjectId(session.get('admin_id'))})
    if request.method == 'POST':
        namaPengguna = request.form['namaPengguna']
        password = request.form['password']

        doc = {
            'namaPengguna': namaPengguna,
            'password': password
        }
        
        db.admin.insert_one(doc)
        return redirect(url_for("adminDataAdmin"))
        
    return render_template('tambahDataAdmin.html', admin=admin)

@app.route('/editDataAdmin/<string:_id>', methods=["GET", "POST"])
@admin_login_required
def edit_data_admin(_id):
    admin = db.admin.find_one({'_id': ObjectId(session.get('admin_id'))})
    if request.method == 'POST':
        namaPengguna = request.form['namaPengguna']
        password = request.form['password']

        doc = {
            'namaPengguna': namaPengguna,
            'password': password
        }
        
        # Update database
        db.admin.update_one({'_id': ObjectId(_id)}, {'$set': doc})
        return redirect(url_for('adminDataAdmin'))
    
    data = db.admin.find_one({'_id': ObjectId(_id)})
    return render_template('editDataAdmin.html', data=data, admin=admin)

@app.route('/hapusDataAdmin/<string:_id>', methods=["GET", "POST"])
@admin_login_required
def hapus_data_admin(_id):
    db.admin.delete_one({'_id': ObjectId(_id)})
    return redirect(url_for('adminDataAdmin'))
# route admin produk end


# route admin riwayat pemesanan start
@app.route('/adminRiwayatPemesanan', methods=['GET', 'POST'])
@admin_login_required
def adminRiwayatPemesanan():
    admin = db.admin.find_one({'_id': ObjectId(session.get('admin_id'))})
    page = int(request.args.get('page', 1))
    per_page = 5
    total_products = db.riwayatPemesanan.count_documents({})
    total_pages = (total_products + per_page - 1) // per_page

    # Urutkan data berdasarkan tanggal pemesanan (desc) dan paginasi
    riwayatPemesanan = list(db.riwayatPemesanan.find().sort('tanggal_pemesanan', pymongo.DESCENDING).skip((page - 1) * per_page).limit(per_page))

    return render_template('adminRiwayatPemesanan.html', riwayatPemesanan=riwayatPemesanan, page=page, total_pages=total_pages, admin=admin)
# route admin riwayat pemesanan end

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('nama-lengkap', None)
    session.pop('email', None)
    session.pop('namaPengguna', None)
    flash('Anda telah Keluar')
    return redirect(url_for('index'))

@app.route('/adminLogout')
def admin_logout():
    session.pop('admin_id', None)
    flash('Admin telah Keluar')
    return redirect(url_for('admin_login'))


@app.route('/dataPribadi', methods=['GET', 'POST'])
@login_required
def dataPribadi():
    user_id = session.get('user_id')
    if request.method == 'POST':
        # Handle form submission to update user data
        updated_data = {
            "namaLengkap": request.form.get('namaLengkap'),
            "nomorTelepon": request.form.get('nomorTelepon'),
            "namaPengguna": request.form.get('namaPengguna'),
            "tanggalLahir": request.form.get('tanggalLahir'),
            "email": request.form.get('email'),
            "alamat": request.form.get('alamat')
        }
        db.users.update_one({'_id': ObjectId(user_id)}, {'$set': updated_data})
        return redirect(url_for('dataPribadi'))
    
    users = db.users.find_one({'_id': ObjectId(user_id)})
    return render_template('dataPribadi.html', users=users)
#izin nambahin buat liat tampilannya


@app.route('/riwayatPemesanan', methods=['GET', 'POST'])
@login_required
def riwayat_pemesanan():
    user_id = session.get('user_id')
    if user_id:
        riwayatPemesanan = list(db.riwayatPemesanan.find({'user_id': ObjectId(user_id)}))
        return render_template('riwayatPemesanan.html', riwayatPemesanan=riwayatPemesanan)
    else:
        return redirect(url_for('login'))  # Arahkan ke halaman login jika user_id tidak ditemukan di session


# @app.route('/generate_pdf', methods=['GET'])
# def generate_pdf():
#     # Ambil data riwayat pemesanan dari MongoDB
#     riwayatPemesanan = list(db.riwayatPemesanan.find().sort('_id', DESCENDING))

#     # Menghasilkan PDF
#     response = make_response(generate_pdf_from_data(riwayatPemesanan))
#     response.headers['Content-Type'] = 'application/pdf'
#     response.headers['Content-Disposition'] = 'inline; filename=riwayat_pemesanan.pdf'
#     return response

# def generate_pdf_from_data(riwayatPemesanan):
#     buffer = BytesIO()

#     # Menggunakan landscape untuk halaman
#     doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))

#     # Konten PDF
#     elements = []

#     # Judul laporan
#     styles = getSampleStyleSheet()
#     title_style = styles['Title']
#     elements.append(Paragraph("Laporan Riwayat Pemesanan", title_style))

#     # Tabel riwayat pemesanan
#     data = [["Nama", "No Handphone", "Nama Produk", "Total dus dan Harga Produk", "Tanggal Pemesanan", "Alamat"]]
#     for data_pemesanan in riwayatPemesanan:
#         # Menangani kasus di mana kunci mungkin tidak ada di dalam data
#         nama_lengkap = data_pemesanan.get('nama_lengkap', '')
#         nomor_telepon = data_pemesanan.get('nomor_telepon', '')
#         nama_produk = data_pemesanan.get('nama_produk', '')
#         jumlah_produk = data_pemesanan.get('jumlah_produk', '')
#         tanggal_pemesanan = data_pemesanan.get('tanggal_pemesanan', '')
#         alamat = data_pemesanan.get('alamat', '')

#         data.append([nama_lengkap, nomor_telepon, nama_produk, jumlah_produk, tanggal_pemesanan, alamat])

#     # Tabel
#     table = Table(data, repeatRows=1)
#     table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Background color for header row
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),             # Align all cells to center
#         ('GRID', (0, 0), (-1, -1), 1, colors.black)        # Add border to cells
#     ]))

#     elements.append(table)

#     # Membuat dokumen PDF
#     doc.build(elements)

#     # Mengembalikan buffer PDF
#     buffer.seek(0)
#     return buffer.read()



if __name__ == '__main__':
    app.run(debug=True, port=8000, host="0.0.0.0")
    