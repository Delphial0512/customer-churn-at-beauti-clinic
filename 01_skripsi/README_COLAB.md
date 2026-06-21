# Menjalankan notebook skripsi di Colab

1. Buka `customer_churn_at_beauti_clinic_thesis.ipynb` di GitHub.
2. Klik tombol **Open in Colab**.
3. Jalankan sel instalasi. Sel itu memakai `%pip`, bukan `pip install` polos.
4. Buka panel **Files** di sisi kiri. Klik **Upload**.
5. Upload `TRANSAKSI.xlsx`, `SURVEY.xlsx`, dan `PATIENT.xlsx`.
6. Jalankan seluruh notebook dari atas ke bawah.

File unggahan Colab masuk ke `/content/`. Jadi konfigurasi notebook otomatis membaca:

```text
/content/TRANSAKSI.xlsx
/content/SURVEY.xlsx
/content/PATIENT.xlsx
```

Jangan mengedit file `.ipynb` sebagai JSON. Buka notebook dari GitHub atau Colab, lalu edit langsung dalam sel kode dan sel teks.

Kalau nama file Excel beda, ubah bagian `PATH_TRX`, `PATH_SURVEY`, atau `PATH_PATIENT` di Blok 1. Contoh:

```python
PATH_TRX = Path("/content/transaksi_beauti_juni.xlsx")
```
