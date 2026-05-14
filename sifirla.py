import subprocess
import sys
# yeni güncelleme geldiğinde temiz tabanı güncellemek için terminal kodu. git tag -f temiz-taban git push origin -f temiz-taban

def fabrikayi_sifirla():
    print("--- FABRİKA STERİLİZASYON PROTOKOLÜ BAŞLATILDI ---")
    
    komutlar = [
        # 0. GÜVENLİK KİLİDİ: Farklı bir dalda veya detached durumda olma riskine karşı önce kesinlikle 'main' dalına geç!
        ("Ana dala (main) kilitleniliyor...", ["git", "checkout", "main"]),
        
        # 1. Yereldeki tüm dosyaları buluttaki kirlenmiş main'e değil, betona döktüğümüz 'temiz-taban' noktasına zorla çek
        ("Dosyalar mühürlü 'temiz-taban' noktasına çekiliyor...", ["git", "reset", "--hard", "temiz-taban"]),
        
        # 2. YZ'nin yeni oluşturduğu tüm ekstra klasörleri, modülleri ve isimsiz dosyaları (untracked) jilet gibi temizle
        ("Kalıntı klasörler ve yabancı dosyalar çöpe atılıyor...", ["git", "clean", "-fd"]),
        
        # 3. STERİLİZASYON: Bu temiz halini buluta ZORLA fırlat ki buluttaki kirlenmiş ajan geçmişi tamamen silinsin
        ("Buluttaki kirlenmiş depo sterilize ediliyor (Force Push)...", ["git", "push", "origin", "main", "--force"])
    ]
    
    for aciklama, komut in komutlar:
        print(aciklama)
        try:
            # check=True sayesinde komutlardan biri bile tökezlerse sistem anında durur, yarı yolda bırakmaz
            subprocess.run(komut, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as hata:
            print(f"\n[KRİTİK HATA] İşlem şurada başarısız oldu: {' '.join(komut)}")
            print(f"Hata Detayı:\n{hata.stderr}")
            print("Sistem güvenliği için sterilizasyon derhal durduruldu.")
            return

    print("\n[BAŞARILI] Fabrika ve Bulut tamamen temizlendi! Ortam yepyeni bir üretime 100% hazır.")

if __name__ == "__main__":
    print("DİKKAT: Bu işlem YZ'nin ürettiği tüm kodları, eklediği kütüphaneleri hem tabletten hem buluttan KALICI olarak silecek.")
    onay = input("Fabrikayı orijinal temiz tabana döndürmeyi onaylıyor musun? (e/h): ")
    
    if onay.lower() == 'e':
        fabrikayi_sifirla()
    else:
        print("Sıfırlama protokolü iptal edildi. Mevcut dosyalar korunuyor.")