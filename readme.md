# 🚀 Selenium GUI

Aplikasi GUI Python modern untuk menjalankan automation Selenium secara paralel, terintegrasi dengan Docker Selenoid, multi-script, dan editor kode Python interaktif. Cocok untuk QA Engineer, developer, maupun pengguna awam yang ingin melakukan pengujian otomatisasi web dengan mudah.

---

## ✨ Fitur Utama

- **GUI Otomasi Modern**  
  Jalankan script Selenium secara paralel (multi-thread) dengan visualisasi status dan log real-time.

- **Editor Kode Python Terintegrasi**  
  Edit, buat, dan kelola script Python langsung dari aplikasi dengan syntax highlighting, line number, dan fitur pencarian/replace.

- **Integrasi Docker Selenoid**  
  Mendukung eksekusi remote browser via Selenoid (Chrome/Firefox) baik lokal maupun server.

- **Manajemen Script Otomatis**  
  Pilih script, refresh list, rename, save, dan buat script baru langsung dari GUI.

- **Konfigurasi Mudah**  
  Atur jumlah worker, headless mode, delay, dan mode Docker/Local hanya dengan klik.

- **Log Terminal Interaktif**  
  Monitoring log eksekusi, error, dan status dengan tampilan terminal CLI di dalam aplikasi.

- **Multi-Platform**  
  Berjalan di Windows, Linux, dan macOS (dengan Python 3.8+).

---

## 📁 Struktur Folder

```
test_docker/
├── .env
├── base_gui.py
├── Base.py
├── Scripts/
│   └── (script Python automation Anda)
├── selenoid/
│   └── config/
│       └── browsers.json
├── assets/
│   └── icon.ico
│   └── python_icon.png
├── requirements.txt
```

---

## ⚡ Cara Instalasi & Menjalankan

1. **Clone Repository**
   ```bash
   git clone https://github.com/Maseylan/tilabs_selenium_test_docker.git
   cd test_docker
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Konfigurasi Selenoid (Opsional)**
   - Pastikan Selenoid berjalan di Docker dan port 4444 terbuka.
   - Edit `.env` untuk URL Selenoid dan target browser.

4. **Jalankan GUI**
   ```bash
   python base_gui.py
   ```

5. **Tambahkan Script**
   - Simpan script Python Anda di folder `Scripts/`.
   - Script harus memiliki fungsi `main()` sebagai entry point.

---

## 🧪 Contoh Script Automation

Buat file di folder `Scripts/` misal `example_script.py`:

```python
SCRIPT_NAME = "Contoh Script"
SCRIPT_DESCRIPTION = "Script Selenium sederhana untuk demo"

def main(gui_instance=None):
    print("Script berjalan!")
    # Tambahkan logika Selenium Anda di sini
```

---

## 🛠 Troubleshooting

- **Port 4444 Error**  
  Pastikan port 4444 tidak digunakan aplikasi lain dan sudah di-mapping di Docker.

- **Selenoid Tidak Terkoneksi**  
  Cek konfigurasi `SELENOID_URL` di `.env`.

- **Script Tidak Muncul**  
  Pastikan file script berekstensi `.py` dan ada fungsi `main()`.

- **Error Webdriver**  
  Pastikan driver Chrome/Firefox sudah terinstall atau gunakan mode Docker.

---

## 📚 Dokumentasi & Referensi

- [Selenium Documentation](https://www.selenium.dev/documentation/)
- [Selenoid Docs](https://aerokube.com/selenoid/latest/)
- [Tkinter GUI](https://docs.python.org/3/library/tkinter.html)
- [Pygments Syntax Highlighting](https://pygments.org/)

---

## 👨‍💻 Kontributor

- [MasEylan](https://github.com/Maseylan)  
  *QA Engineer & Python Enthusiast*

---

## 📄 Lisensi

MIT License

---

> **Aplikasi ini dibuat untuk memudahkan pengujian otomatisasi web secara visual dan efisien. Silakan kembangkan sesuai