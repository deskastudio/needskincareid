// sidebar start
const toggleSidebar = () => {
    const sidebar = document.getElementById('sidebar');
    if (sidebar.classList.contains('collapsed')) {
      sidebar.classList.remove('collapsed');
      sidebar.classList.add('expanded');
    } else {
      sidebar.classList.remove('expanded');
      sidebar.classList.add('collapsed');
    }
  };

document.getElementById('toggle-link').addEventListener('click', toggleSidebar);

document.getElementById('dashboard-link').addEventListener('click', function() {
document.getElementById('dashboard-link').addEventListener('click', toggleSidebar);
    document.querySelectorAll('.nav-link').forEach(item => {
        item.classList.remove('active');
    });
    this.classList.add('active');
});
document.getElementById('produk-link').addEventListener('click', function() {
document.getElementById('produk-link').addEventListener('click', toggleSidebar);
    document.querySelectorAll('.nav-link').forEach(item => {
        item.classList.remove('active');
    });
    this.classList.add('active');
});
document.getElementById('pelanggan-link').addEventListener('click', function() {
document.getElementById('pelanggan-link').addEventListener('click', toggleSidebar);
    document.querySelectorAll('.nav-link').forEach(item => {
        item.classList.remove('active');
    });
    this.classList.add('active');
});
document.getElementById('pemesanan-link').addEventListener('click', function() {
document.getElementById('pemesanan-link').addEventListener('click', toggleSidebar);
    document.querySelectorAll('.nav-link').forEach(item => {
        item.classList.remove('active');
    });
    this.classList.add('active');
});
document.getElementById('pembayaran-link').addEventListener('click', function() {
document.getElementById('pembayaran-link').addEventListener('click', toggleSidebar);
    document.querySelectorAll('.nav-link').forEach(item => {
        item.classList.remove('active');
    });
    this.classList.add('active');
});
document.getElementById('produkTerlaris-link').addEventListener('click', function() {
document.getElementById('produkTerlaris-link').addEventListener('click', toggleSidebar);
    document.querySelectorAll('.nav-link').forEach(item => {
        item.classList.remove('active');
    });
    this.classList.add('active');
});
document.getElementById('bannerHomepage-link').addEventListener('click', function() {
document.getElementById('bannerHomepage-link').addEventListener('click', toggleSidebar);
    document.querySelectorAll('.nav-link').forEach(item => {
        item.classList.remove('active');
    });
    this.classList.add('active');
});
document.getElementById('footer-link').addEventListener('click', function() {
document.getElementById('footer-link').addEventListener('click', toggleSidebar);
    document.querySelectorAll('.nav-link').forEach(item => {
        item.classList.remove('active');
    });
    this.classList.add('active');
});
document.getElementById('admin-link').addEventListener('click', function() {
document.getElementById('admin-link').addEventListener('click', toggleSidebar);
    document.querySelectorAll('.nav-link').forEach(item => {
        item.classList.remove('active');
    });
    this.classList.add('active');
});
document.getElementById('riwayatPemesanan-link').addEventListener('click', function() {
document.getElementById('riwayatPemesanan-link').addEventListener('click', toggleSidebar);
    document.querySelectorAll('.nav-link').forEach(item => {
        item.classList.remove('active');
    });
    this.classList.add('active');
});
document.getElementById('keluar-link').addEventListener('click', function() {
document.getElementById('keluar-link').addEventListener('click', toggleSidebar);
    document.querySelectorAll('.nav-link').forEach(item => {
        item.classList.remove('active');
    });
    this.classList.add('active');
});
// sidebar end