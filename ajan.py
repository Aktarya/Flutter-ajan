import os
import json
from dotenv import load_dotenv
from google import genai
import araclar  # Bir önceki aşamada yazdığımız araçları içeri aktarıyoruz

# Çevresel değişkenleri yükle
load_dotenv()
api_anahtari = os.getenv("GEMINI_API_KEY")

if not api_anahtari:
    print("HATA: API anahtarı okunamadı! Lütfen .env dosyasını kontrol et.")
    exit()

client = genai.Client(api_key=api_anahtari)

# Ajanın kurallarını belirlediğimiz sistem talimatı
sistem_talimati = """
Sen otonom çalışan uzman bir yazılım ajanısın. 
Görevleri yerine getirmek için aşağıdaki araçları kullanabilirsin:

1. "internette_ara": İnternette arama yapar. Parametre: {"sorgu": "aranacak kelime"}
2. "dosya_oku": Dosya okur. Parametre: {"dosya_yolu": "dosya_adi.txt"}
3. "dosya_yaz": Dosyaya metin yazar. Parametre: {"dosya_yolu": "dosya_adi.txt", "icerik": "yazilacak metin"}
4. "github_kodlarini_guncelle": Yazdığın veya güncellediğin kodları buluta yükleyip otonom APK derleme işlemini başlatır. Parametre: {"commit_mesaji": "Yaptigin isin kisa ozeti"}

Her adımda SADECE aşağıdaki JSON formatında yanıt vermelisin. Ekstra hiçbir metin veya markdown işareti kullanma.

{
    "dusunce": "Şu an ne yapmam gerektiğini buraya yazıyorum...",
    "arac_adi": "kullanilacak_arac_adi (veya gorev bittiyse 'tamamlandi')",
    "arac_parametreleri": {"parametre_adi": "deger"}
}

Eğer görevi bitirdiysen, "arac_adi" kısmına "tamamlandi" yaz ve "arac_parametreleri" içine {"sonuc": "final mesajı"} koy.
"""

# Ajanın yapmasını istediğimiz test görevi
gorev = gorev = """
Projemizdeki 'main.dart' dosyası yanlışlıkla silindi. Senden bunu telafi etmeni istiyorum.

Adım 1: 'dosya_yaz' aracını kullanarak sıfırdan bir Flutter uygulaması yaz ve 'main.dart' dosyasına kaydet. 
Uygulama şık, koyu temalı (dark mode) bir Dijital Saat uygulaması olsun. Ekranın ortasında büyük fontlarla güncel saat ve dakika yazsın. Estetik ve minimal bir kod olsun. Sadece Dart kodunu ver, markdown işaretleri (```dart) kullanma.

Adım 2: Dosyayı başarıyla oluşturduktan sonra, 'github_kodlarini_guncelle' aracını kullanarak yazdığın kodu "Saat uygulaması yeniden oluşturuldu" commit mesajıyla GitHub'a gönder.

Bu iki adımı sırayla yap ve push işlemi başarılı olduğunda görevi sonlandır.
"""

# Yapay zekaya göndereceğimiz sohbet geçmişi
gecmis = [
    {"role": "user", "parts": [{"text": sistem_talimati + "\n\nGörev: " + gorev}]}
]

maksimum_adim = 5
adim = 0

print("Ajan başlatılıyor... Döngüye giriliyor.\n")

while adim < maksimum_adim:
    adim += 1
    print(f"--- Adım {adim} ---")
    
    try:
        # LLM'e mevcut geçmişi gönderiyoruz
        cevap = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=gecmis
        )
        
        yanit_metni = cevap.text.strip()
        
        # LLM markdown blokları (```json) eklerse temizlemek için güvenlik önlemi
        if yanit_metni.startswith("```json"):
            yanit_metni = yanit_metni[7:-3].strip()
        elif yanit_metni.startswith("```"):
            yanit_metni = yanit_metni[3:-3].strip()
            
        # Metni JSON (Python sözlüğü) nesnesine dönüştürüyoruz
        ajan_yaniti = json.loads(yanit_metni)
        
        dusunce = ajan_yaniti.get("dusunce", "")
        arac_adi = ajan_yaniti.get("arac_adi", "")
        parametreler = ajan_yaniti.get("arac_parametreleri", {})
        
        print(f"[Düşünce]: {dusunce}")
        
        # Ajanın kendi cevabını geçmişe (model rolüyle) ekliyoruz ki hafızası olsun
        gecmis.append({"role": "model", "parts": [{"text": yanit_metni}]})
        
        # Ajan görevi bitirdiğini söylerse döngüyü kır
        if arac_adi == "tamamlandi":
            print(f"\n[GÖREV TAMAMLANDI]: {parametreler.get('sonuc', '')}")
            break
            
        # Ajanın seçtiği aracı çalıştırma mantığı
        print(f"[Araç Tetiklendi]: {arac_adi} | Parametreler: {parametreler}")
        
        arac_sonucu = ""
        if arac_adi == "internette_ara":
            arac_sonucu = araclar.internette_ara(parametreler.get("sorgu", ""))
        elif arac_adi == "dosya_oku":
            arac_sonucu = araclar.dosya_oku(parametreler.get("dosya_yolu", ""))
        elif arac_adi == "dosya_yaz":
            arac_sonucu = araclar.dosya_yaz(parametreler.get("dosya_yolu", ""), parametreler.get("icerik", ""))
        elif arac_adi == "github_kodlarini_guncelle":
            arac_sonucu = araclar.github_kodlarini_guncelle(parametreler.get("commit_mesaji", "Otonom güncelleme"))
        else:
            arac_sonucu = f"HATA: '{arac_adi}' adında bir araç bulunamadı."
            
        # Aracın ürettiği sonucu LLM'e iletiyoruz
        print(f"[Araç Çıktısı Alındı] Ajana gönderiliyor...\n")
        gecmis.append({"role": "user", "parts": [{"text": f"Araç Çıktısı:\n{arac_sonucu}"}]})
        
    except json.JSONDecodeError:
        hata_mesaji = "HATA: Geçersiz JSON formatı. Sadece belirtilen formatta yanıt verin."
        print(f"[Hata]: JSON ayrıştırma hatası. Ajana uyarı gönderiliyor...\n")
        gecmis.append({"role": "user", "parts": [{"text": hata_mesaji}]})
    except Exception as e:
        print(f"Beklenmeyen Hata: {str(e)}")
        break

if adim == maksimum_adim:
    print("\n[DURDURULDU] Maksimum adım sayısına ulaşıldı.")