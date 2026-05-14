import os
import json
from dotenv import load_dotenv
from google import genai
import araclar  # Tüm araçlarımızın bulunduğu modül
import time

# Çevresel değişkenleri yükle
load_dotenv()
api_anahtari = os.getenv("GEMINI_API_KEY")

if not api_anahtari:
    print("HATA: API anahtarı okunamadı! Lütfen .env dosyasını kontrol et.")
    exit()

# Yeni nesil Client başlatma
client = genai.Client(api_key=api_anahtari)

# Ajanın anayasasını ve aşamalı boru hattı (Pipeline) stratejisini belirliyoruz
sistem_talimati = """
Sen üst düzey bir otonom yazılım mimarı ve Flutter APK üretim hattı yöneticisisin. 
Görevin, sana verilen projeyi baştan sona kusursuz bir şekilde inşa etmek, varlıklarını üretmek ve derlemeye hazır hale getirmektir.

Şu aşamalı stratejiyi (Pipeline) takip etmelisin:
1. ALTYAPI VE ANALİZ: İhtiyaç duyulan kütüphaneleri, cihaz izinlerini ve uygulama adını ayarla.
2. MANTIK VE ARAYÜZ: Gerekli Dart kodlarını, ekranları ve iş mantığını lib/ dizinine yaz.
3. GÖRSEL MOTOR: Uygulama ikonunu, logolarını ve arayüzde kullanılacak SVG varlıklarını otonom araçlarla üret.
4. SENKRONİZASYON: Tüm sistem kusursuz olduğunda kodları GitHub'a gönderip Actions derlemesini tetikle.

Kullanabileceğin Araç Cephaneliği:

1. "internette_ara": Map-Reduce örümcek motoruyla derinlemesine araştırma yapar. Parametre: {"sorgu_amaci": "araştırılacak konu"}
2. "dosya_oku": Belirtilen dosyanın içeriğini okur. Parametre: {"dosya_yolu": "yol/dosya.ext"}
3. "dart_kodu_yaz": Sadece 'lib/' klasörü içine Dart kodu yazar. Parametre: {"dosya_alt_yolu": "main.dart", "icerik": "kodlar"}
4. "kutuphane_ekle": pubspec.yaml dosyasına kütüphane ekler. Eğer kodların içinde 'provider', 'flutter_svg' gibi harici paketler kullanıyorsan, DART KODUNU YAZMADAN ÖNCE MUTLAKA 'kutuphane_ekle' aracıyla bu paketleri pubspec.yaml'a ekle! Aksi takdirde derleyici kütüphaneyi bulamaz ve çöker. Parametre: {"paket_adi": "provider", "surum": "any"}
5. "uygulama_ismini_degistir": Android uygulamasının adını günceller. Parametre: {"yeni_isim": "Harika Uygulama"}
6. "android_izni_ekle": AndroidManifest.xml'e cihaz izni ekler. Parametre: {"izin_adi": "INTERNET"}
7. "asset_dosyasi_yaz": 'assets/' klasörüne veri yazar. Parametre: {"dosya_alt_yolu": "veri.json", "icerik": "metin"}
8. "asset_klasorunu_tanimla": pubspec.yaml dosyasına assets/ dizinini kaydeder. Parametre: {}
9. "svg_uret": Otonom ressam/kritik döngüsüyle SVG varlığı üretir. görsel alan daha önce üretilmiş bir görsele geri dönüp üzerinde çalışmayı sağlarken dosya yolu üretilen görselin direkt olarak assets/ klasörü altında tam adı ve uzantısıyla otomatik yerleşimini sağlar. Parametre: {"gorsel_alani": "arkaplan", "dosya_alt_yolu": "bg.svg", "tema_ozeti": "koyu, neon mavi", "istek": "Soyut dalgalar"}
10. "android_logosu_uret": Otonom XML vektör döngüsüyle logo üretir ve Manifest'e bağlar. Parametre: {"istek": "Minimalist saat ikonu", "tema_ozeti": "koyu tema, estetik"}
11. "dosya_sil": lib/ veya assets/ altındaki gereksiz dosyaları ve boş klasörleri temizler. Parametre: {"dosya_yolu": "lib/eski.dart"}
12. "kullaniciya_sor": İNSAN DÖNGÜSÜ FRENİ. Tıkandığında, emin olamadığında, kritik bir tasarım kararı alman gerektiğinde veya kullanıcıdan yönlendirme/onay istediğin HERHANGİ BİR ANDA sormaktan çekinme. Parametre: {"soru": "Kullanıcıya sorulacak net soru"}

KRİTİK KURAL: Her adımda SADECE aşağıdaki JSON formatında yanıt vermelisin. Açıklama, fazladan metin veya markdown bloğu (```json vb.) KULLANMA.

{
    "dusunce": "Şu an boru hattının hangi aşamasındayım, neyi hedefliyorum ve neden bu aracı seçtim...",
    "arac_adi": "kullanilacak_arac_adi (veya tüm boru hattı bittiyse 'tamamlandi')",
    "arac_parametreleri": {"parametre_adi": "deger"}
}

Eğer tüm üretim hattını başarıyla tamamlayıp GitHub'a pushladıysan, "arac_adi" kısmına "tamamlandi" yaz ve parametre olarak {"sonuc": "Final özet mesajı"} ilet.
"""

# Test Görevi (Tüm boru hattını çalıştıracak zengin bir senaryo)
gorev = """
Otonom Üretim Hattını (Pipeline) devreye al. Hedefimiz: 'Zaman Çarkı' adında, Pomodoro tekniğine dayalı şık bir odaklanma ve verimlilik uygulaması geliştirmek.

Adım 1: Uygulama adını 'Zaman Çarkı' yap ve internet iznini ekle. Gerekirse durum yönetimi için 'provider' kütüphanesini ekle.
Adım 2: 'assets/' klasörünü pubspec.yaml'a tanımla. Ardından 'svg_uret' aracıyla arayüzde kullanmak üzere koyu temalı, soyut dairesel bir arkaplan SVG'si üret.
Adım 3: 'android_logosu_uret' aracıyla uygulamaya yakışır, modern ve vektörel bir Pomodoro/Saat ikonu çizdir.
Adım 4: 'dart_kodu_yaz' aracını kullanarak ana işlevselliği barındıran temiz, modüler ve estetik bir Pomodoro sayacı kodla.
Adım 5: Geliştirme sürecinin uygun gördüğün kritik bir noktasında 'kullaniciya_sor' aracını tetikleyerek tema renkleri veya varsayılan çalışma süresi (örn: 25 dk mı 30 dk mı?) hakkında bana danış.
Adım 6: Tüm entegrasyon bitince kodları GitHub'a gönder ('Zaman Çarkı üretim hattı tamamlandı' mesajıyla) ve Actions sürecini başlat.
"""

# Yapay zekaya göndereceğimiz sohbet geçmişi
gecmis = [
    {"role": "user", "parts": [{"text": sistem_talimati + "\n\nGörev: " + gorev}]}
]

# Çoklu araç orkestrasyonu için adım limitini genişlettik
maksimum_adim = 30
adim = 0

print("🚀 Otonom Üretim Hattı (Pipeline) Başlatılıyor...\n" + "="*50)

while adim < maksimum_adim:
    adim += 1
    print(f"\n▶️ --- Adım {adim} ---")
    # --- API ÇAĞRISI İÇİN OTONOM TEKRAR (RETRY) MOTORU ---
    maksimum_deneme = 5
    deneme = 0
    cevap = None
    
    while deneme < maksimum_deneme:
        try:
            cevap = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=gecmis
            )
            break  # Başarılı olursa iç döngüyü anında kır ve devam et
            
        except Exception as api_hatasi:
            deneme += 1
            hata_metni = str(api_hatasi).lower()
            
            # 429 Kota, yoğunluk veya 500 sunucu hatalarını yakala
            if "too many requests" in hata_metni or "quota" in hata_metni or "overloaded" in hata_metni or "500" in hata_metni or "503" in hata_metni:
                bekleme_suresi = 10 * deneme  # Her başarısızlıkta süreyi uzat (10s, 20s, 30s...)
                print(f"⚠️ [Sunucu Yoğunluğu / Kota Freni]: API şu an yanıt veremiyor. Ajanın hafızası korunarak {bekleme_suresi} saniye bekleniyor... (Deneme: {deneme}/{maksimum_deneme})")
                time.sleep(bekleme_suresi)
            else:
                # Beklenmeyen başka bir hata ise doğrudan yukarıya fırlat
                raise api_hatasi
                
    if not cevap:
        print("\n❌ [KRİTİK HATA]: Sunucu 5 denemeye rağmen yanıt vermedi. Boru hattı duraklatılıyor.")
        break
    # --- TEKRAR MOTORU BİTİŞİ ---
    try:
        
        yanit_metni = cevap.text.strip()
        
        # LLM istemsizce markdown formatı eklerse sterilize et
        if yanit_metni.startswith("```json"):
            yanit_metni = yanit_metni[7:-3].strip()
        elif yanit_metni.startswith("```"):
            yanit_metni = yanit_metni[3:-3].strip()
            
        ajan_yaniti = json.loads(yanit_metni)
        
        dusunce = ajan_yaniti.get("dusunce", "")
        arac_adi = ajan_yaniti.get("arac_adi", "")
        parametreler = ajan_yaniti.get("arac_parametreleri", {})
        
        print(f"💡 [Düşünce]: {dusunce}")
        
        # Ajanın yanıtını model rolüyle geçmişe işle
        gecmis.append({"role": "model", "parts": [{"text": yanit_metni}]})
        
        if arac_adi == "tamamlandi":
            araclar.dart_importlarini_sanitize_et()
            araclar.github_kodlarini_guncelle("ajan güncellemesi")
            print("\n" + "🎉"*25)
            print(f"✅ [ÜRETİM HATTI TAMAMLANDI]: {parametreler.get('sonuc', '')}")
            print("🎉"*25)
            break
            
        print(f"⚙️ [Araç Tetiklendi]: {arac_adi}")
        
        # --- GÜVENLİ VE DİNAMİK ARAÇ HARİTALAMA (MAPPING) ---
        arac_sonucu = ""
        
        if arac_adi == "internette_ara":
            arac_sonucu = araclar.internette_ara(parametreler.get("sorgu_amaci", ""))
        elif arac_adi == "dosya_oku":
            arac_sonucu = araclar.dosya_oku(parametreler.get("dosya_yolu", ""))
        elif arac_adi == "dart_kodu_yaz":
            arac_sonucu = araclar.dart_kodu_yaz(parametreler.get("dosya_alt_yolu", ""), parametreler.get("icerik", ""))
        elif arac_adi == "kutuphane_ekle":
            arac_sonucu = araclar.kutuphane_ekle(parametreler.get("paket_adi", ""), parametreler.get("surum", "any"))
        elif arac_adi == "uygulama_ismini_degistir":
            arac_sonucu = araclar.uygulama_ismini_degistir(parametreler.get("yeni_isim", ""))
        elif arac_adi == "android_izni_ekle":
            arac_sonucu = araclar.android_izni_ekle(parametreler.get("izin_adi", ""))
        elif arac_adi == "asset_dosyasi_yaz":
            arac_sonucu = araclar.asset_dosyasi_yaz(parametreler.get("dosya_alt_yolu", ""), parametreler.get("icerik", ""))
        elif arac_adi == "asset_klasorunu_tanimla":
            arac_sonucu = araclar.asset_klasorunu_tanimla()
        elif arac_adi == "svg_uret":
            arac_sonucu = araclar.svg_uret(
                parametreler.get("gorsel_alani", ""),
                parametreler.get("dosya_alt_yolu", ""),
                parametreler.get("tema_ozeti", ""),
                parametreler.get("istek", "")
            )
        elif arac_adi == "android_logosu_uret":
            arac_sonucu = araclar.android_logosu_uret(parametreler.get("istek", ""), parametreler.get("tema_ozeti", ""))
        elif arac_adi == "dosya_sil":
            arac_sonucu = araclar.dosya_sil(parametreler.get("dosya_yolu", ""))
        elif arac_adi == "github_kodlarini_guncelle":
            arac_sonucu = araclar.github_kodlarini_guncelle(parametreler.get("commit_mesaji", "Otonom boru hattı güncellemesi"))
        elif arac_adi == "kullaniciya_sor":
            arac_sonucu = araclar.kullaniciya_sor(parametreler.get("soru", ""))
        else:
            arac_sonucu = f"HATA: '{arac_adi}' adında bir araç cephanelikte bulunamadı. Talimatlardaki geçerli araç isimlerini kontrol et."
            
        # Aracın fiziksel çıktısını LLM'e geri besliyoruz
        gecmis.append({"role": "user", "parts": [{"text": f"Araç Çıktısı:\n{arac_sonucu}"}]})
        
    except json.JSONDecodeError:
        hata_mesaji = "HATA: Kritik JSON format ihlali! Yanıtın doğrudan ayrıştırılabilir ham bir JSON nesnesi olmalıdır."
        print("⚠️ [Sistem Uyarısı]: JSON Format Hatası. Ajana düzeltme talimatı iletiliyor...")
        gecmis.append({"role": "user", "parts": [{"text": hata_mesaji}]})
    except Exception as e:
        print(f"\n❌ [KRİTİK SİSTEM HATASI]: {str(e)}")
        break

if adim == maksimum_adim:
    print("\n🛑 [BORU HATTI DURDURULDU]: Güvenlik amacıyla maksimum otonomi adım limitine (30) ulaşıldı.")