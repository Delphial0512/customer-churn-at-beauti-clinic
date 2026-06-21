# Hapus repository lama lalu ganti dengan paket ini

Sebelum menghapus repo lama, simpan ZIP ini di komputer. Penghapusan repo menghapus file, commit, issue, dan pengaturan repo tersebut.

## 1. Hapus repository lama

1. Buka repository lama: `Delphial0512/customer-churn-at-beauti-clinic`.
2. Klik tab **Settings** pada repository. Bukan Settings akun GitHub.
3. Klik **General** jika halaman belum berada di sana.
4. Scroll sampai bagian **Danger Zone**.
5. Pilih **Delete this repository**.
6. Ikuti teks konfirmasi yang diminta GitHub. Ketik nama repo persis seperti yang tampil di layar.
7. Klik tombol penghapusan terakhir.

Jangan pilih **Delete account**. Yang dihapus hanya repository.

## 2. Buat repository baru dengan nama sama

1. Klik ikon `+` di kanan atas GitHub lalu pilih **New repository**.
2. Isi nama repository: `customer-churn-at-beauti-clinic`.
3. Pilih **Public** jika kamu mau tombol Colab bisa dibuka tanpa proses izin tambahan. Kode dan template di paket ini tidak berisi data customer asli.
4. Pilih **Private** kalau ada aturan kampus atau perusahaan. Colab perlu diberi izin akses ke GitHub saat notebook private dibuka.
5. Jangan centang pilihan untuk membuat README, `.gitignore`, atau License. Paket ini sudah punya file tersebut.
6. Klik **Create repository**.

## 3. Upload paket baru

1. Ekstrak file ZIP ini.
2. Buka repository baru lalu klik **Add file** → **Upload files**.
3. Drag semua isi folder `customer-churn-at-beauti-clinic-final` ke area upload. Jangan upload ZIP-nya.
4. Pastikan folder `01_skripsi`, `02_business_dashboard`, `data`, dan `src` ikut terbaca. File `.gitignore`, `README.md`, dan `requirements.txt` juga harus ikut.
5. Di kotak commit, tulis:

   ```text
   chore: replace repository with clean project structure
   ```

6. Kolom deskripsi commit boleh kosong.
7. Pilih **Commit directly to the main branch** lalu klik **Commit changes**.

## 4. Cek setelah upload

Buka halaman utama repository. Daftar file harus menampilkan `README.md`, folder `01_skripsi`, folder `02_business_dashboard`, `src`, `requirements.txt`, dan `.gitignore`.

Lalu buka `01_skripsi/notebooks/customer_churn_at_beauti_clinic_thesis.ipynb`. Tombol Colab ada pada sel teks pertama. Bila tombol tidak dapat membuka notebook, cek bahwa nama repo, branch `main`, dan path file sama seperti yang tertulis di README.

Folder `data/raw/` memang kosong di GitHub. Data customer asli masuk ke Colab melalui upload file, atau ke laptop lewat `data/raw/`.
