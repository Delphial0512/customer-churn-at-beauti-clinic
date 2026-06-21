# Menjalankan dashboard di Windows

Jangan buka file ini dari ZIP. Ekstrak ZIP dulu.

1. Masuk ke folder `02_business_dashboard`.
2. Pastikan ada tiga file: `app.py`, `requirements_dashboard.txt`, dan `start_dashboard_windows.bat`.
3. Klik dua kali `start_dashboard_windows.bat`.
4. Saat pertama dijalankan, Windows membuka jendela hitam dan memasang library dashboard. Internet perlu menyala.
5. Browser biasanya terbuka sendiri. Kalau belum, buka `http://localhost:8501`.
6. Upload `Scoring_Customer_Aktif_Lengkap.xlsx` dari output notebook.

Jendela hitam harus tetap terbuka saat dashboard dipakai. Tekan `Ctrl + C` di jendela itu untuk menghentikan dashboard.

Pesan `py is not recognized` berarti launcher Python tidak ada. Launcher ini sudah mencoba `py`, `python`, lalu `python3`. Kalau semuanya gagal, install Python 3 dari situs Python, lalu centang **Add python.exe to PATH** saat instalasi.

Kalau nama file berubah jadi `start_dashboard_windows.bat.txt`, aktifkan **File name extensions** di Windows Explorer lalu hapus `.txt` terakhir.
