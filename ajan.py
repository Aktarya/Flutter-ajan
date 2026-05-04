import os
from dotenv import load_dotenv
from google import genai

# Şifreyi güvenli .env dosyasından çekiyoruz
load_dotenv()
api_anahtari = os.getenv("GEMINI_API_KEY")

# API anahtarı okunabilmiş mi diye kontrol ediyoruz
if not api_anahtari:
    print("HATA: API anahtarı okunamadı! Lütfen .env dosyasının içini ve adını kontrol et.")
    exit()

# Yeni kütüphane ile ajanı başlatıyoruz
client = genai.Client(api_key=api_anahtari)

gorev = """
Sen uzman ve vizyoner bir Flutter UI geliştiricisisin. 
Bana sıfırdan tek bir `main.dart` dosyası içinde çalışacak bir Saat uygulaması yaz. 

Uygulamanın estetiği tamamen 'Steampunk' tarzında olmalıdır. 
- Arka plan koyu kahverengi ve paslı bakır tonlarında olmalı.
- Kadran tasarımı eski bir Viktoryan cep saatini andırmalı, altın veya pirinç renkli kalın ibreler (akrep/yelkovan) kullanılmalı.
- Tasarımı sadece statik bırakma; ekrana Steampunk temasını güçlendirecek dekoratif (belki animasyonlu veya şekilsel) dişli çark detayları ekle.
- Kod mimarisini temiz tut. Sadece Dart kodunu ver, Markdown işaretleri (```dart) dışında hiçbir ekstra metin veya açıklama yazma.
"""

print("Ajan düşünmeye başladı... Lütfen bekle.")

# Kodu üretiyoruz
cevap = client.models.generate_content(model='gemini-2.5-flash',contents=gorev,)

# Gelen cevabın içinden sadece kodu ayıklayıp kaydediyoruz
kod_metni = cevap.text.replace('```dart', '').replace('```', '').strip()

with open("main.dart", "w", encoding="utf-8") as dosya:
    dosya.write(kod_metni)

print("İşlem tamam! Flutter kodu 'main.dart' dosyasına kaydedildi.")