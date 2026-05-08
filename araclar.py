import os
from ddgs import DDGS
import subprocess

# 1. ARAÇ: DOSYA OKUMA
def dosya_oku(dosya_yolu):
    """Verilen dosya yolundaki metni okur ve geri döndürür."""
    try:
        with open(dosya_yolu, "r", encoding="utf-8") as dosya:
            icerik = dosya.read()
            return icerik
    except FileNotFoundError:
        return f"HATA: '{dosya_yolu}' adında bir dosya bulunamadı."
    except Exception as hata:
        return f"HATA: Dosya okunurken bir sorun oluştu: {hata}"

# 2. ARAÇ: DOSYA YAZMA
def dosya_yaz(dosya_yolu, icerik):
    """Belirtilen yola, belirtilen içeriği yazar."""
    try:
        with open(dosya_yolu, "w", encoding="utf-8") as dosya:
            dosya.write(icerik)
        return f"BAŞARILI: İçerik '{dosya_yolu}' dosyasına kaydedildi."
    except Exception as hata:
        return f"HATA: Dosya yazılamadı: {hata}"

# 3. ARAÇ: İNTERNETTE ARAMA
def internette_ara(sorgu):
    """DuckDuckGo üzerinden arama yapar ve ilk 3 sonucu metin olarak döndürür."""
    try:
        ddgs = DDGS()
        # Sadece 3 sonuç alıyoruz ki yapay zekanın kafası karışmasın
        sonuclar = ddgs.text(sorgu, max_results=3) 
        
        if not sonuclar:
            return "Sonuç bulunamadı."
            
        metin_sonucu = "İnternet Arama Sonuçları:\n\n"
        for sonuc in sonuclar:
            metin_sonucu += f"Başlık: {sonuc['title']}\nİçerik: {sonuc['body']}\nBağlantı: {sonuc['href']}\n\n"
            
        return metin_sonucu
    except Exception as hata:
        return f"HATA: İnternet araması başarısız oldu: {hata}"


def github_kodlarini_guncelle(commit_mesaji="Ajan guncellemesi"):
    """
    Değişiklikleri otomatik olarak GitHub'a gönderir (Push).
    Bu araç, GitHub Actions üzerinden APK derleme sürecini tetikler.
    """
    komutlar = [
        ["git", "add", "."],
        ["git", "commit", "-m", commit_mesaji],
        ["git", "push"]
    ]
    
    log = ""
    for komut in komutlar:
        try:
            # shell=False kullanarak güvenliği artırıyoruz
            sonuc = subprocess.run(komut, capture_output=True, text=True, check=True)
            log += f"{' '.join(komut)} -> Başarılı\n"
        except subprocess.CalledProcessError as hata:
            return f"HATA ({' '.join(komut)}): {hata.stderr}"
            
    return f"Sistem GitHub'a başarıyla senkronize edildi. APK derlemesi bulutta başladı.\nDetaylar:\n{log}"

# --- TEST BÖLÜMÜ ---
# Bu dosyayı doğrudan çalıştırdığımızda araçların çalışıp çalışmadığını test edelim.
if __name__ == "__main__":
    print("Araçlar test ediliyor...\n")
    
    # 1. Test: Arama yap
    arama_sonucu = internette_ara("Flutter 3.19 yenilikleri nelerdir?")
    print(arama_sonucu)
    
    # 2. Test: Bu arama sonucunu bir dosyaya yaz
    yazma_sonucu = dosya_yaz("test_notlari.txt", arama_sonucu)
    print(yazma_sonucu)
    
    # 3. Test: Yazdığımız dosyayı oku
    okuma_sonucu = dosya_oku("test_notlari.txt")
    print(f"\nDosyadan okunan verinin uzunluğu: {len(okuma_sonucu)} karakter.")
