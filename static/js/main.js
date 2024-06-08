$(document).ready(function() {
    const toggleSidebar = () => {
        const sidebar = $('#sidebar');
        if (sidebar.hasClass('collapsed')) {
            sidebar.removeClass('collapsed').addClass('expanded');
        } else {
            sidebar.removeClass('expanded').addClass('collapsed');
        }
    };

    $('#toggle-link').click(function(event) {
        event.preventDefault();
        toggleSidebar();
    });

    $('.nav-link:not(#toggle-link)').click(function(event) {
        event.preventDefault();
        $('.nav-link').removeClass('active');
        $(this).addClass('active');
    });

    $('#dashboard-link').click(toggleSidebar);
    $('#produk-link').click(toggleSidebar);
    $('#pelanggan-link').click(toggleSidebar);
    $('#pemesanan-link').click(toggleSidebar);
    $('#pembayaran-link').click(toggleSidebar);
    $('#produkTerlaris-link').click(toggleSidebar);
    $('#bannerHomepage-link').click(toggleSidebar);
    $('#footer-link').click(toggleSidebar);
    $('#admin-link').click(toggleSidebar);
    $('#riwayatPemesanan-link').click(toggleSidebar);
    $('#keluar-link').click(toggleSidebar);
});
