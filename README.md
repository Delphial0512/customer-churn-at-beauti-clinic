# Customer Churn at Beauti Clinic

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Delphial0512/customer-churn-at-beauti-clinic/blob/main/01_skripsi/notebooks/customer_churn_at_beauti_clinic_thesis.ipynb)

Repository ini memisahkan kebutuhan skripsi dan pemakaian operasional tanpa membuat dua model yang berbeda.

`01_skripsi` berisi notebook untuk cleaning data, pembentukan fitur, XGBoost, Optuna, evaluasi testing, SHAP, dan scoring customer aktif. `02_business_dashboard` membaca file scoring jadi daftar follow-up yang dapat dipakai tanpa membuka kode.

## Folder proyek

```text
customer-churn-at-beauti-clinic/
├── 01_skripsi/notebooks/customer_churn_at_beauti_clinic_thesis.ipynb
├── 02_business_dashboard/
│   ├── app.py
│   ├── start_dashboard_windows.bat
│   └── requirements_dashboard.txt
├── data/
│   ├── raw/                 # file asli, tidak masuk GitHub
│   └── template/            # contoh format file tanpa data asli
├── src/customer_churn_pipeline.py
├── outputs/                 # hasil run, tidak masuk GitHub
├── requirements.txt
├── REPLACE_REPOSITORY.md
└── .gitignore
```

## Jalankan notebook di Colab

Buka notebook melalui tombol Colab di atas. Jalankan sel instalasi. Setelah itu upload `TRANSAKSI.xlsx`, `SURVEY.xlsx`, dan `PATIENT.xlsx` dari panel **Files** di sisi kiri Colab. Notebook membaca file dari `/content/`.

Output scoring ada di:

```text
/content/outputs/scoring/Scoring_Customer_Aktif_Lengkap.xlsx
```

File itu dipakai oleh dashboard.

## Jalankan di laptop

Simpan tiga file input pada `data/raw/`, lalu jalankan perintah ini dari folder proyek:

```bash
python -m pip install -r requirements.txt
python src/customer_churn_pipeline.py
```

Kalau menjalankan notebook lokal, buka Jupyter dari folder proyek supaya folder `data/raw/` terbaca dengan benar.

File `src/customer_churn_pipeline.py` menghitung tabel, model, SHAP detail, dan file scoring. Saat dipanggil sebagai script, gambar tree dan gambar SHAP tidak dibuat supaya proses lokal tidak berat. Notebook tetap membuat gambar tersebut. Atur `GENERATE_TREE_PLOT=1` dan `GENERATE_SHAP_PLOTS=1` bila menjalankan script dan perlu gambar itu.

## Dashboard operasional

Sesudah notebook selesai, ambil `Scoring_Customer_Aktif_Lengkap.xlsx`. Buka folder `02_business_dashboard` lalu klik dua kali `start_dashboard_windows.bat`. Pertama kali, file tersebut membuat `.venv` dan memasang Streamlit. Browser akan membuka `http://localhost:8501`.

Upload file scoring pada dashboard. Tabel risiko tinggi bisa langsung diunduh sebagai Excel untuk follow-up.

## Definisi label churn

`frequency_pred` adalah jumlah kunjungan pada periode prediksi setelah masa observasi. Notebook memberi `churn = 1` saat `frequency_pred = 0`. Artinya customer tidak punya transaksi pada tiga bulan prediksi yang dipakai oleh model, bukan pernyataan bahwa customer pasti tidak akan kembali lagi.

## Data customer

Jangan masukkan `data/raw/`, `outputs/`, model, token, atau API key ke GitHub. Folder itu sudah masuk `.gitignore`.

Gunakan `data/template/` untuk melihat kolom yang dibutuhkan. Template hanya berisi data contoh.
