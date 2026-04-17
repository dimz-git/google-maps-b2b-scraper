import time
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By

def bersihkan_alamat(teks):
    teks = teks.replace('\n', ', ')
    # Menghapus simbol kotak aneh (Icon Google Maps)
    teks = re.sub(r'[^\x20-\x7E]+', '', teks) 
    # Menghapus tanda minus atau spasi kosong di paling depan
    return teks.strip(', -').strip()

def bersihkan_hp(teks):
    teks = teks.replace('\n', '')
    # Hanya izinkan angka, spasi, tanda kurung, dan strip untuk nomor telepon
    teks = re.sub(r'[^\d\+\-\(\)\s]+', '', teks)
    return teks.strip()

def run_scraper():
    print("[INFO] Memulai Selenium WebDriver...")
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    
    driver = webdriver.Chrome(options=options)
    query = "cafe in jakarta selatan"
    print(f"[INFO] Mencari tempat: '{query}' di Google Maps...")
    
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
    driver.get(url)
    time.sleep(5) 
    
    data_scraped = []
    target_limit = 20
    
    try:
        print("[INFO] Memuat daftar lokasi (Scrolling)...")
        daftar_toko = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')
        
        while len(daftar_toko) < target_limit:
            driver.execute_script("arguments[0].scrollIntoView();", daftar_toko[-1])
            time.sleep(2.5) 
            
            daftar_toko_baru = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')
            if len(daftar_toko_baru) == len(daftar_toko):
                break 
            daftar_toko = daftar_toko_baru
            
        batas_akhir = min(target_limit, len(daftar_toko))
        print(f"[INFO] Berhasil memuat {len(daftar_toko)} lokasi di memori. Memproses {batas_akhir} toko...")
        
        for i in range(batas_akhir):
            try:
                daftar_toko_aktif = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')
                toko_diklik = daftar_toko_aktif[i]
                
                nama_kedai = toko_diklik.get_attribute('aria-label')
                if not nama_kedai:
                    nama_kedai = "Nama Tidak Terbaca"
                nama_kedai = bersihkan_alamat(nama_kedai)
                
                print(f"[{i+1}/{batas_akhir}] Mengekstrak detail: {nama_kedai}")
                driver.execute_script("arguments[0].click();", toko_diklik)
                time.sleep(3.5)
                
                try:
                    alamat = driver.find_element(By.CSS_SELECTOR, '[data-item-id="address"]').text
                    alamat = bersihkan_alamat(alamat)
                except:
                    alamat = "Alamat Tidak Ditemukan"
                    
                try:
                    nomor_hp = driver.find_element(By.CSS_SELECTOR, '[data-item-id^="phone:"]').text
                    nomor_hp = bersihkan_hp(nomor_hp)
                except:
                    nomor_hp = "Tidak Mencantumkan Nomor HP"
                
                data_scraped.append({
                    'Nama Kedai': nama_kedai,
                    'Alamat Lengkap': alamat,
                    'Nomor Handphone': nomor_hp
                })
                
            except Exception as loop_err:
                print(f"[WARNING] Gagal memproses baris ke-{i+1}: {loop_err}")
                
    except Exception as e:
        print(f"[ERROR] Kesalahan sistem: {e}")
        
    finally:
        print("[INFO] Pencarian selesai. Menutup Chrome...")
        driver.quit()
        
        if len(data_scraped) > 0:
            file_name = "Data_Premium_Kopi_Jakarta.csv"
            df = pd.DataFrame(data_scraped)
            df.to_csv(file_name, index=False, encoding='utf-8')
            print(f"[SUCCESS] Penyimpanan berhasil. Disimpan ke: '{file_name}'")
        else:
            print("[FAILED] Tidak ada data yang berhasil diekstrak.")

if __name__ == '__main__':
    run_scraper()
