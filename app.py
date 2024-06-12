import os
from posixpath import dirname, join
import re
from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, flash, jsonify, render_template, request, redirect, session, url_for
from pymongo import MongoClient
import bcrypt
from werkzeug.utils import secure_filename 
from werkzeug.security import check_password_hash

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  str(os.environ.get("DB_NAME"))

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

users_collection = db['users']

app = Flask(__name__)
app.secret_key = os.urandom(24)

def is_valid_admin():
    return 'admin_id' in session


@app.route('/')
def index():
    produkTerlaris = db.produkTerlaris.find()
    return render_template('index.html', produkTerlaris=produkTerlaris)

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
    return render_template('produk.html')


# route admin dashboard start
@app.route('/adminDashboard')
def adminDashboard():
    if is_valid_admin():
        return render_template('adminDashboard.html')
    else: 
        return redirect(url_for('admin_login'))
# route admin dashboard end



# route admin produk start
@app.route('/adminProduk')
def adminProduk():
    if is_valid_admin():
        products = db.products.find()
        return render_template('adminProduk.html', products=products)
    else:
        return redirect(url_for('admin_login'))


@app.route('/tambahDataProduk', methods=['GET', 'POST'])
def tambah_data_produk():
    if request.method == 'POST':
        jenisSkincare = request.form['jenisSkincare']
        namaProduk = request.form['namaProduk']
        hargaPerPcs = request.form['hargaPerPcs']
        totalDus = request.form['totalDus']
        totalHarga = request.form['totalHarga']
        photo = request.files['photo']
        
        if photo:
            nama_file_asli = photo.filename
            nama_file_gambar = secure_filename(nama_file_asli)
            file_path = f'./static/assets/imgProduk/{nama_file_gambar}'
            photo.save(file_path)
        else:
            nama_file_gambar = None
            
        doc = {
            'jenis_skincare': jenisSkincare,
            'nama_produk': namaProduk,
            'harga_per_pcs': hargaPerPcs,
            'total_dus': totalDus,
            'total_harga': totalHarga,
            'photo': nama_file_gambar
        }
        
        db.products.insert_one(doc)
        return redirect(url_for("adminProduk"))
        
    return render_template('tambahDataProduk.html')

@app.route('/editDataProduk/<string:_id>', methods=["GET", "POST"])
def edit_data_produk(_id):
    if request.method == 'POST':
        jenisSkincare = request.form['jenisSkincare']
        namaProduk = request.form['namaProduk']
        hargaPerPcs = request.form['hargaPerPcs']
        totalDus = request.form['totalDus']
        totalHarga = request.form['totalHarga']
        photo = request.files['photo']

        # Inisialisasi nama_file_gambar dengan nilai default
        nama_file_gambar = None

        # Simpan file jika ada
        if photo:
            nama_file_asli = photo.filename
            nama_file_gambar = secure_filename(nama_file_asli)
            file_path = f'./static/assets/imgProduk/{nama_file_gambar}'
            photo.save(file_path)
        
        # Buat dictionary untuk update
        doc = {
            'jenis_skincare': jenisSkincare,
            'nama_produk': namaProduk,
            'harga_per_pcs': hargaPerPcs,
            'total_dus': totalDus,
            'total_harga': totalHarga
        }

        # Tambahkan nama_file_gambar ke dictionary jika ada
        if nama_file_gambar:
            doc['photo'] = nama_file_gambar
        
        # Update database
        db.products.update_one({'_id': ObjectId(_id)}, {'$set': doc})
        return redirect(url_for('adminProduk'))
    
    data = db.products.find_one({'_id': ObjectId(_id)})
    return render_template('editDataProduk.html', data=data)

@app.route('/hapusDataProduk/<string:_id>', methods=["GET", "POST"])
def hapus_data_produk(_id):
    db.products.delete_one({'_id': ObjectId(_id)})
    return redirect(url_for('adminProduk'))
# route admin produk end



# route admin pelanggan start
@app.route('/adminPelanggan', methods=['GET'])
def adminPelanggan():
    if is_valid_admin():
        users = db.users.find()
        page = int(request.args.get('page', 1))
        per_page = 5  # Number of users per page
        total_users = users_collection.count_documents({})
        total_pages = (total_users + per_page - 1) // per_page

        users = list(users_collection.find().skip((page - 1) * per_page).limit(per_page))

        return render_template('adminPelanggan.html', users=users, page=page, total_pages=total_pages)
    else:
        return redirect(url_for('admin_login'))
    

@app.route('/hapusDataPelanggan/<string:_id>', methods=["GET", "POST"])
def hapus_data_pelanggan(_id):
    db.users.delete_one({'_id': ObjectId(_id)})
    return redirect(url_for('adminPelanggan'))
# route admin pelanggan end



# route admin pemesanan start
@app.route('/adminPemesanan')
def adminPemesanan():
    if is_valid_admin():
        return render_template('adminPemesanan.html')
    else:
        return redirect(url_for('admin_login'))
# route admin pemesanan end



# route admin pembayaran start
@app.route('/adminPembayaran', methods=['GET'])
def adminPembayaran():
    if is_valid_admin():
        pembayaran = db.pembayaran.find()
        page = int(request.args.get('page', 1))
        per_page = 5  # Number of products per page
        total_products = db.pembayaran.count_documents({})
        total_pages = (total_products + per_page - 1) // per_page

        pembayaran = list(db.pembayaran.find().skip((page - 1) * per_page).limit(per_page))

        return render_template('adminPembayaran.html', pembayaran=pembayaran, page=page, total_pages=total_pages)
    else:
        return redirect(url_for('admin_login'))

@app.route('/tambahDataPembayaran', methods=['GET', 'POST'])
def tambah_data_pembayaran():
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
        
    return render_template('tambahDataPembayaran.html')

@app.route('/editDataPembayaran/<string:_id>', methods=["GET", "POST"])
def edit_data_pembayaran(_id):
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
    return render_template('editDataPembayaran.html', data=data)

@app.route('/hapusDataPembayaran/<string:_id>', methods=["GET", "POST"])
def hapus_data_pembayaran(_id):
    db.pembayaran.delete_one({'_id': ObjectId(_id)})
    return redirect(url_for('adminPembayaran'))
# route admin pembayaran end



# route produk terlaris start
@app.route('/adminProdukTerlaris', methods=['GET'])
def adminProdukTerlaris():
    if is_valid_admin():
        produkTerlaris = db.produkTerlaris.find()
        return render_template('adminProdukTerlaris.html', produkTerlaris=produkTerlaris)
    else:
        return redirect(url_for('admin_login'))

@app.route('/tambahDataProdukTerlaris', methods=['GET', 'POST'])
def tambah_data_produk_terlaris():
    if request.method == 'POST':
        jenisSkincare = request.form['jenisSkincare']
        namaProduk = request.form['namaProduk']
        hargaPerPcs = request.form['hargaPerPcs']
        totalDus = request.form['totalDus']
        totalHarga = request.form['totalHarga']
        photo = request.files['photo']
        
        if photo:
            nama_file_asli = photo.filename
            nama_file_gambar = secure_filename(nama_file_asli)
            file_path = f'./static/assets/imgProdukTerlaris/{nama_file_gambar}'
            photo.save(file_path)
        else:
            nama_file_gambar = None
            
        doc = {
            'jenis_skincare': jenisSkincare,
            'nama_produk': namaProduk,
            'harga_per_pcs': hargaPerPcs,
            'total_dus': totalDus,
            'total_harga': totalHarga,
            'photo': nama_file_gambar
        }
        
        db.produkTerlaris.insert_one(doc)
        return redirect(url_for("adminProdukTerlaris"))
        
    return render_template('tambahDataProdukTerlaris.html')

@app.route('/editDataProdukTerlaris/<string:_id>', methods=["GET", "POST"])
def edit_data_produk_terlaris(_id):
    if request.method == 'POST':
        jenisSkincare = request.form['jenisSkincare']
        namaProduk = request.form['namaProduk']
        hargaPerPcs = request.form['hargaPerPcs']
        totalDus = request.form['totalDus']
        totalHarga = request.form['totalHarga']
        photo = request.files['photo']

        # Inisialisasi nama_file_gambar dengan nilai default
        nama_file_gambar = None

        # Simpan file jika ada
        if photo:
            nama_file_asli = photo.filename
            nama_file_gambar = secure_filename(nama_file_asli)
            file_path = f'./static/assets/imgProdukTerlaris/{nama_file_gambar}'
            photo.save(file_path)
        
        # Buat dictionary untuk update
        doc = {
            'jenis_skincare': jenisSkincare,
            'nama_produk': namaProduk,
            'harga_per_pcs': hargaPerPcs,
            'total_dus': totalDus,
            'total_harga': totalHarga
        }

        # Tambahkan nama_file_gambar ke dictionary jika ada
        if nama_file_gambar:
            doc['photo'] = nama_file_gambar
        
        # Update database
        db.produkTerlaris.update_one({'_id': ObjectId(_id)}, {'$set': doc})
        return redirect(url_for('adminProdukTerlaris'))
    
    data = db.produkTerlaris.find_one({'_id': ObjectId(_id)})
    return render_template('editDataProdukTerlaris.html', data=data)

@app.route('/hapusDataProdukTerlaris/<string:_id>', methods=["GET", "POST"])
def hapus_data_produk_terlaris(_id):
    db.produkTerlaris.delete_one({'_id': ObjectId(_id)})
    return redirect(url_for('adminProdukTerlaris'))
# route produk terlaris end



# route banner homepage start
@app.route('/adminBannerHomepage')
def adminBannerHomepage():
    if is_valid_admin():
        bannerHomepage = db.bannerHomepage.find()
        page = int(request.args.get('page', 1))
        per_page = 5  # Number of products per page
        total_banner = db.bannerHomepage.count_documents({})
        total_pages = (total_banner + per_page - 1) // per_page

        bannerHomepage = list(db.bannerHomepage.find().skip((page - 1) * per_page).limit(per_page))

        return render_template('adminBannerHomepage.html', bannerHomepage=bannerHomepage, page=page, total_pages=total_pages)
    else:
        return redirect(url_for('admin_login'))

@app.route('/tambahDataBannerHomepage', methods=['GET', 'POST'])
def tambah_data_banner_homepage():
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
        
    return render_template('tambahDataBannerHomepage.html')

@app.route('/editDataBannerHomepage/<string:_id>', methods=["GET", "POST"])
def edit_data_banner_homepage(_id):
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
    return render_template('editDataBannerHomepage.html', data=data)

@app.route('/hapusDataBannerHomepage/<string:_id>', methods=["GET", "POST"])
def hapus_data_banner_homepage(_id):
    db.bannerHomepage.delete_one({'_id': ObjectId(_id)})
    return redirect(url_for('adminBannerHomepage'))
# route produk terlaris end



# route data admin start
@app.route('/adminDataAdmin')
def adminDataAdmin():
    if is_valid_admin():
        admin = db.admin.find()
        page = int(request.args.get('page', 1))
        per_page = 5  # Number of products per page
        total_admin = db.admin.count_documents({})
        total_pages = (total_admin + per_page - 1) // per_page

        admin = list(db.admin.find().skip((page - 1) * per_page).limit(per_page))

        return render_template('adminDataAdmin.html', admin=admin, page=page, total_pages=total_pages)
    else:
        return redirect(url_for('admin_login'))

@app.route('/tambahDataAdmin', methods=['GET', 'POST'])
def tambah_data_admin():
    if request.method == 'POST':
        namaPengguna = request.form['namaPengguna']
        password = request.form['password']

        doc = {
            'namaPengguna': namaPengguna,
            'password': password
        }
        
        db.admin.insert_one(doc)
        return redirect(url_for("adminDataAdmin"))
        
    return render_template('tambahDataAdmin.html')

@app.route('/editDataAdmin/<string:_id>', methods=["GET", "POST"])
def edit_data_admin(_id):
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
    return render_template('editDataAdmin.html', data=data)

@app.route('/hapusDataAdmin/<string:_id>', methods=["GET", "POST"])
def hapus_data_admin(_id):
    db.admin.delete_one({'_id': ObjectId(_id)})
    return redirect(url_for('adminDataAdmin'))
# route admin produk end



# route admin footer start
@app.route('/adminFooter', methods=['GET'])
def adminFooter():
    if is_valid_admin():
        footer = db.footer.find()
        page = int(request.args.get('page', 1))
        per_page = 5  # Number of products per page
        total_footer = db.footer.count_documents({})
        total_pages = (total_footer + per_page - 1) // per_page

        footer = list(db.footer.find().skip((page - 1) * per_page).limit(per_page))

        return render_template('adminFooter.html', footer=footer, page=page, total_pages=total_pages)
    else:
        return redirect(url_for('admin_login'))

@app.route('/tambahDataFooter', methods=['GET', 'POST'])
def tambah_data_footer():
    if request.method == 'POST':
        socialMedia = request.form['socialMedia']
        username = request.form['username']
        linkSosmed = request.form['linkSosmed']

        doc = {
            'socialMedia': socialMedia,
            'username': username,
            'linkSosmed': linkSosmed
        }
        
        db.footer.insert_one(doc)
        return redirect(url_for("adminFooter"))
        
    return render_template('tambahDataFooter.html')

@app.route('/editDataFooter/<string:_id>', methods=["GET", "POST"])
def edit_data_footer(_id):
    if request.method == 'POST':
        socialMedia = request.form['socialMedia']
        username = request.form['username']
        linkSosmed = request.form['linkSosmed']

        doc = {
            'socialMedia': socialMedia,
            'username': username,
            'linkSosmed': linkSosmed
        }
        
        # Update database
        db.footer.update_one({'_id': ObjectId(_id)}, {'$set': doc})
        return redirect(url_for('adminFooter'))
    
    data = db.footer.find_one({'_id': ObjectId(_id)})
    return render_template('editDataFooter.html', data=data)

@app.route('/hapusDataFooter/<string:_id>', methods=["GET", "POST"])
def hapus_data_footer(_id):
    db.footer.delete_one({'_id': ObjectId(_id)})
    return redirect(url_for('adminFooter'))
# route admin footer end



# route admin riwayat pemesanan start
@app.route('/adminRiwayatPemesanan')
def adminRiwayatPemesanan():
    if is_valid_admin():
        return render_template('adminRiwayatPemesanan.html')
    else:
        return redirect(url_for('admin_login'))
# route admin riwayat pemesanan end

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/adminLogout')
def admin_logout():
    # Hapus data admin dari sesi
    session.pop('admin_id', None)
    # Redirect ke halaman login admin atau halaman lain yang sesuai
    return redirect(url_for('index'))

@app.route('/dataPribadi')
def dataPribadi():
    return render_template('dataPribadi.html')
#izin nambahin buat liat tampilannya

@app.route('/pemesanan')
def pemesanan():
    return render_template('pemesanan.html')
#izin nambahin buat liat tampilannya

@app.route('/detailPemesanan')
def detailPemesanan():
    return render_template('detailPemesanan.html')


@app.route('/riwayatPemesanan')
def riwayatPemesanan():
    return render_template('riwayatPemesanan.html')

if __name__ == '__main__':
    app.run(debug=True, port=8000, host="0.0.0.0")
    