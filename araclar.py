import os
from ddgs import DDGS
import subprocess
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types
import urllib.request
import urllib.error
import time
from functools import wraps

# --- 1. ZIRH MOTORU ---
def api_zirhi(maksimum_deneme=5):
    """API çağrılarını sunucu hatalarına karşı koruyan kalkan."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            deneme = 0
            while deneme < maksimum_deneme:
                try:
                    return func(*args, **kwargs)
                except Exception as hata:
                    deneme += 1
                    hata_metni = str(hata).lower()
                    if any(k in hata_metni for k in ["too many requests", "quota", "overloaded", "500", "503", "boş_yanıt"]):
                        bekleme = 8 * deneme
                        print(f"🔄 [API Freni]: Sunucu yoğun. {bekleme}s bekleniyor... (Deneme: {deneme}/{maksimum_deneme})")
                        time.sleep(bekleme)
                    else:
                        raise hata
            raise Exception(f"Sunucu {maksimum_deneme} denemeye rağmen yanıt vermedi.")
        return wrapper
    return decorator

# --- 2. ORTAK ELÇİ FONKSİYON ---
# Zırhı bu elçiye giydiriyoruz. Artık tüm araçlar mesajlarını bu elçi üzerinden gönderecek.
@api_zirhi() 
def zirhli_mesaj_gonder(sohbet_nesnesi, mesaj_metni):
    """Gemini sohbet nesnelerinden (chat) güvenli ve zırhlı mesaj gönderir."""
    resp = sohbet_nesnesi.send_message(mesaj_metni)
    if not resp or not resp.text:
        raise Exception("boş_yanıt")
    return resp
# --- 3. ARAMA MOTORU İÇİN İKİNCİ ELÇİ FONKSİYON ---
@api_zirhi()
def zirhli_icerik_uret(client_nesnesi, talimat_metni):
    """Gemini Client üzerinden güvenli ve zırhlı tekil içerik üretir (generate_content)."""
    resp = client_nesnesi.models.generate_content(model='gemini-2.5-flash', contents=talimat_metni)
    if not resp or not resp.text:
        raise Exception("boş_yanıt")
    return resp
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

def dart_kodu_yaz(dosya_alt_yolu, icerik):
    """
    Sadece 'lib/' klasörü içine kod yazar. Klasör yoksa sessizce üretir.
    Örn: YZ 'screens/home.dart' derse, doğrudan 'lib/screens/home.dart' konumuna yazar.
    """
    # YZ dalgınlıkla parametrenin başına lib/ yazdıysa temizle (çiftleme olmasın)
    if dosya_alt_yolu.startswith("lib/"):
        dosya_alt_yolu = dosya_alt_yolu[4:]
        
    tam_yol = os.path.join("lib", dosya_alt_yolu)
    
    try:
        # Klasörü otomatik aç
        os.makedirs(os.path.dirname(tam_yol), exist_ok=True)
        with open(tam_yol, "w", encoding="utf-8") as dosya:
            dosya.write(icerik.strip())
        return f"BAŞARILI: Dart kodu '{tam_yol}' konumuna yazıldı."
    except Exception as hata:
        return f"HATA (Yazma): {hata}"

# Arama sonuçlarını kalıcı olarak tutacağımız global sözlük
ARAMA_HAFIZASI = {}

def sayfa_icerigini_cek(url):
    """
    Standart Python kütüphaneleriyle çalışan hafif bir 'Web Örümceği'.
    Sayfaya girer, HTML, JS ve CSS kodlarını budayarak sadece saf metni süzer.
    """
    try:
        # Sitelerin bot engellemesini aşmak için standart bir tarayıcı kimliği (User-Agent) takınıyoruz
        istek = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(istek, timeout=10) as yanit:
            html = yanit.read().decode('utf-8', errors='ignore')
            
            # Script ve Style bloklarını kökünden temizle
            html = re.sub(r'<script[\s\S]*?</script>', '', html, flags=re.IGNORECASE)
            html = re.sub(r'<style[\s\S]*?</style>', '', html, flags=re.IGNORECASE)
            
            # Kalan tüm HTML etiketlerini temizle
            saf_metin = re.sub(r'<[^>]+>', ' ', html)
            
            # Fazla boşlukları, sekmeleri ve satır atlamaları daralt
            saf_metin = re.sub(r'\s+', ' ', saf_metin).strip()
            
            # Ajana fazla yüklenmemek için her sayfanın en zengin ilk 30.000 karakterini alıyoruz
            return saf_metin[:30000]
            
    except Exception as hata:
        return f"[Sayfa Okunamadı: {hata}]"


# 3. ARAÇ: OTONOM ÖRÜMCEKLİ VE ALT AJANLI İNTERNET ARAMA MOTORU
def internette_ara(sorgu_amaci):
    """
    Map-Reduce mantığıyla çalışan çok ajanlı internet araştırma modülü.
    Planlar, arar, örümcekle kazır, her siteyi ayrı ajana okutur ve sentezler.
    """
    global ARAMA_HAFIZASI
    
    # Önceden detaylı aranmış bir konuyaysa doğrudan hafızadan ver
    if sorgu_amaci in ARAMA_HAFIZASI:
        return f"ÖNBELLEKTEN GELEN RAPOR:\n{ARAMA_HAFIZASI[sorgu_amaci]}"
        
    try:
        from dotenv import load_dotenv
        load_dotenv()
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # --- 1. AŞAMA: PLANLAYICI AJAN ---
        planlayici_talimat = (
            f"Hedef: '{sorgu_amaci}'. Bu konuyu DuckDuckGo'da en doğru şekilde araştırmak için "
            "sadece en etkili 2 farklı arama anahtar kelimesi üret. Yanıtını sadece virgülle ayırarak ver."
        )
        plan_cevap = zirhli_icerik_uret(client, planlayici_talimat)
        uretilen_sorgular = [s.strip() for s in plan_cevap.text.split(",") if s.strip()]
        
        if not uretilen_sorgular:
            uretilen_sorgular = [sorgu_amaci] # Güvenlik yedeği
            
        # --- 2. AŞAMA: DDGS İLE LİNK TOPLAMA ---
        ddgs = DDGS()
        toplanan_linkler = set()
        
        for sorgu in uretilen_sorgular[:2]:
            sonuclar = ddgs.text(sorgu, max_results=2)
            if sonuclar:
                for sonuc in sonuclar:
                    toplanan_linkler.add(sonuc['href'])
                    
        if not toplanan_linkler:
            return "HATA: Araştırma için geçerli hiçbir web sitesi bağlantısı bulunamadı."
            
        # --- 3. AŞAMA: ÖRÜMCEK VE İŞÇİ AJANLAR (MAP) ---
        isci_raporlari = []
        
        for index, url in enumerate(list(toplanan_linkler)[:3], 1): # En iyi 3 linki işliyoruz
            sayfa_metni = sayfa_icerigini_cek(url)
            
            if "[Sayfa Okunamadı" in sayfa_metni or len(sayfa_metni) < 200:
                continue
                
            # HER SİTE İÇİN İZOLE BİR İŞÇİ AJAN ÇALIŞTIRIYORUZ
            isci_talimat = (
                f"Sen dikkatli bir veri madencisisin. Ana Araştırma Hedefi: '{sorgu_amaci}'\n\n"
                f"Aşağıda bir web sayfasının ham metni var. Bu metni tara, reklamları veya alakasız "
                f"kısımları tamamen yok say. SADECE ana hedefle ilgili somut gerçekleri, çözümleri veya "
                f"varsa kod örneklerini cımbızla çekip net bir şekilde özetle.\n\n"
                f"Web Sayfası İçeriği:\n{sayfa_metni}"
            )
            
            isci_cevap = zirhli_icerik_uret(client, isci_talimat)
            isci_raporlari.append(f"--- Kaynak {index} ({url}) Analizi ---\n{isci_cevap.text.strip()}\n")
            
        if not isci_raporlari:
            return "HATA: Siteler tarandı ancak hedefle ilgili kayda değer bir içerik süzülemedi."
            
        # --- 4. AŞAMA: SENTEZLEYİCİ ÜSTAT AJAN (REDUCE) ---
        tum_raporlar_metni = "\n".join(isci_raporlari)
        sentez_talimat = (
            f"Sen bir başyazar ve kıdemli yazılım mimarısın. Ana Hedef: '{sorgu_amaci}'\n\n"
            f"Aşağıda farklı alt ajanların web sitelerinden topladığı izole raporlar bulunuyor. "
            f"Bu raporları birleştir, çelişkili bilgileri ayıkla ve ana ajanın doğrudan kullanabileceği, "
            f"pratik, net ve kapsamlı bir nihai araştırma raporu hazırla.\n\n"
            f"Toplanan Veriler:\n{tum_raporlar_metni}"
        )
        
        sentez_cevap = zirhli_icerik_uret(client, sentez_talimat)
        nihai_rapor = sentez_cevap.text.strip()
        
        # Sonucu global sözlüğe mühürle
        ARAMA_HAFIZASI[sorgu_amaci] = nihai_rapor
        
        return f"OTONOM ARAŞTIRMA RAPORU:\n{nihai_rapor}"
        
    except Exception as hata:
        return f"HATA (Gelişmiş Arama Motoru): {hata}"

# 4. ARAÇ: KOD GÜNCELLEYİCİ VE YOLLAYICI


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
# 5. ARAÇ: PUBSPEC.YAML'A KÜTÜPHANE EKLEME

def kutuphane_ekle(paket_adi, surum="any"):
    """pubspec.yaml dosyasındaki dependencies bloğuna güvenle kütüphane ekler."""
    dosya_yolu = "pubspec.yaml"
    try:
        if not os.path.exists(dosya_yolu):
            return "HATA: pubspec.yaml bulunamadı."

        with open(dosya_yolu, "r", encoding="utf-8") as dosya:
            satirlar = dosya.readlines()

        # Paket zaten var mı?
        if any(f"  {paket_adi}:" in satir for satir in satirlar):
            return f"BİLGİ: '{paket_adi}' zaten mevcut."

        yeni_satirlar = []
        eklendi = False
        for satir in satirlar:
            yeni_satirlar.append(satir)
            # İlgili bloğu bulup 2 boşluk girintisiyle ekle
            if satir.strip() == "dependencies:" and not satir.startswith(" "):
                yeni_satirlar.append(f"  {paket_adi}: {surum}\n")
                eklendi = True

        if not eklendi:
            return "HATA: 'dependencies:' bloğu bulunamadı."

        with open(dosya_yolu, "w", encoding="utf-8") as dosya:
            dosya.writelines(yeni_satirlar)

        return f"BAŞARILI: Kütüphane eklendi -> {paket_adi}"
    except Exception as hata:
        return f"HATA (Kütüphane): {hata}"



# 6.. ARAÇ: UYGULAMA İSMİNİ GÜNCELLEME
def uygulama_ismini_degistir(yeni_isim):
    """
    AndroidManifest.xml içindeki iskelete dokunmadan, 
    sadece 'android:label' (uygulama adı) değerini güvenle günceller.
    """
    tam_yol = os.path.join("android", "app", "src", "main", "AndroidManifest.xml")
    try:
        if not os.path.exists(tam_yol):
            return "HATA: AndroidManifest.xml dosyası bulunamadı."
            
        with open(tam_yol, "r", encoding="utf-8") as dosya:
            icerik = dosya.read()
            
        # Regex (Düzenli İfade) ile android:label="..." kısmını bulup yenisiyle değiştiriyoruz
        yeni_icerik, degisim_sayisi = re.subn(
            r'(android:label=")([^"]*)(")', 
            rf'\g<1>{yeni_isim}\g<3>', 
            icerik
        )
        
        if degisim_sayisi == 0:
            return "HATA: 'android:label' etiketi bulunamadı, isim güncellenemedi."
            
        with open(tam_yol, "w", encoding="utf-8") as dosya:
            dosya.write(yeni_icerik)
            
        return f"BAŞARILI: Uygulama ismi kalıcı olarak '{yeni_isim}' yapıldı."
    except Exception as hata:
        return f"HATA (İsim Değiştirme): {hata}"

# 7.. ARAÇ: ANDROID İZNİ EKLEME
def android_izni_ekle(izin_adi):
    """
    AndroidManifest.xml dosyasına cihaz izni ekler (Örn: INTERNET, CAMERA).
    İskeleti korur, izni tam olması gereken yere (<application> etiketinden önceye) iliştirir.
    """
    # YZ dalgınlıkla sadece 'internet' yazarsa, resmi Android formatına biz çevirelim
    izin_adi = izin_adi.upper().strip()
    if not izin_adi.startswith("ANDROID.PERMISSION."):
        izin_adi = f"android.permission.{izin_adi}"
        
    tam_yol = os.path.join("android", "app", "src", "main", "AndroidManifest.xml")
    try:
        if not os.path.exists(tam_yol):
            return "HATA: AndroidManifest.xml dosyası bulunamadı."
            
        with open(tam_yol, "r", encoding="utf-8") as dosya:
            satirlar = dosya.readlines()
            
        # İzin zaten eklenmiş mi?
        if any(izin_adi in satir for satir in satirlar):
            return f"BİLGİ: '{izin_adi}' yetkisi manifest'te zaten mevcut."
            
        yeni_satirlar = []
        eklendi = False
        
        for satir in satirlar:
            # Android standartlarına göre izinler <application etiketinden hemen önce tanımlanmalıdır
            if "<application" in satir and not eklendi:
                yeni_satirlar.append(f'    <uses-permission android:name="{izin_adi}"/>\n')
                eklendi = True
            yeni_satirlar.append(satir)
            
        if not eklendi:
            return "HATA: '<application' ana etiket bloğu bulunamadı, izin iliştirilemedi."
            
        with open(tam_yol, "w", encoding="utf-8") as dosya:
            dosya.writelines(yeni_satirlar)
            
        return f"BAŞARILI: Android yetkisi eklendi -> {izin_adi}"
    except Exception as hata:
        return f"HATA (İzin Ekleme): {hata}"
# 8. ARAÇ: ASSET (VARLIK) DOSYASI YAZMA
def asset_dosyasi_yaz(dosya_alt_yolu, icerik):
    """
    Projenin kök dizinindeki 'assets/' klasörüne metin tabanlı (JSON, TXT, SVG vb.) veri yazar.
    Klasör yoksa otomatik ve sessizce üretir. YZ asla kök dizinlerde kaybolmaz.
    """
    # YZ dalgınlıkla parametrenin başına assets/ yazdıysa temizle
    if dosya_alt_yolu.startswith("assets/"):
        dosya_alt_yolu = dosya_alt_yolu[7:]
        
    tam_yol = os.path.join("assets", dosya_alt_yolu)
    
    try:
        os.makedirs(os.path.dirname(tam_yol), exist_ok=True)
        with open(tam_yol, "w", encoding="utf-8") as dosya:
            dosya.write(icerik.strip())
        return f"BAŞARILI: Asset dosyası '{tam_yol}' konumuna güvenle yazıldı."
    except Exception as hata:
        return f"HATA (Asset Yazma): {hata}"

# 9. ARAÇ: PUBSPEC.YAML'A ASSET KLASÖRÜNÜ TANIMLAMA (Akıllı Enjeksiyon)
def asset_klasorunu_tanimla():
    """
    pubspec.yaml içindeki 'flutter:' bloğuna tüm 'assets/' klasörünü tek seferde tanımlar.
    Tehlikeli ayrıştırma (parsing) yapmaz, standart Flutter çapasını kullanır.
    """
    dosya_yolu = "pubspec.yaml"
    try:
        if not os.path.exists(dosya_yolu):
            return "HATA: pubspec.yaml dosyası bulunamadı."
            
        with open(dosya_yolu, "r", encoding="utf-8") as dosya:
            icerik = dosya.read()
            
        # Klasör zaten aktif olarak tanımlanmış mı? (Yorum satırı olmayan tanım)
        if "\n    - assets/" in icerik:
            return "BİLGİ: 'assets/' klasörü pubspec.yaml dosyasında zaten tanımlı. Ekstra işleme gerek yok."
            
        # Standart bir Flutter projesinde 'flutter:' bloğunun altında her zaman şu çapa bulunur:
        capa = "uses-material-design: true"
        
        if capa in icerik:
            # Çapayı bulup hemen altına 2 boşluklu assets: ve 4 boşluklu klasör yolunu mühürlüyoruz
            yeni_icerik = icerik.replace(
                capa,
                f"{capa}\n  assets:\n    - assets/"
            )
            with open(dosya_yolu, "w", encoding="utf-8") as dosya:
                dosya.write(yeni_icerik)
            return "BAŞARILI: Tüm 'assets/' klasörü kalıcı olarak pubspec.yaml'a kaydedildi."
        else:
            return "HATA: pubspec.yaml içinde 'uses-material-design: true' çapası bulunamadı, otomatik enjeksiyon yapılamadı."
            
    except Exception as hata:
        return f"HATA (Asset YAML Kaydı): {hata}"



# Alt ajanların kalıcı hafızalarını tutacağımız küresel sözlük
SVG_OTURUMLARI = {}

# SADECE VE SADECE SVG ÜRETEN RESSAM TALİMATI (Sızıntılar temizlendi)
RESSAM_TALIMATI = (
    "Sen sadece yüksek kaliteli ve ölçeklenebilir SVG kodları yazan dünya standartlarında bir grafik tasarımcısısın. "
    "Kullanıcının isteğine göre sadece ve sadece geçerli SVG kodunu üret. Asla markdown (```svg vb.) blokları veya açıklama metni yazma. "
    "Sadece <svg> ile başlayıp </svg> ile biten ham kodu ver."
)

SVG_KRITIK_TALIMATI = (
    "Sen dünya standartlarında bir SVG kodu denetçisi ve görsel kalite kontrol uzmanısın. "
    "Görevin, Ressam'ın ürettiği SVG kodunu ve projenin Tema Özeti'ni analiz etmektir. "
    "1. TEKNİK HATA: <svg> ve diğer etiketler doğru kapatılmış mı? viewBox tanımlı mı?\n"
    "2. TEMA UYUMU: Çizilen görselin renkleri ve tarzı, verilen Tema Özeti'ne uygun mu?\n"
    "3. GÖRÜNÜRLÜK: Zemin rengi ile görsel rengi çakışıyor mu?\n"
    "Sonucu Sadece Şu Formatla Döndür: \n"
    "- Hata varsa: 'HATA_DENETİMİ: [Teknik hata tanımı ve düzeltme önerisi]'\n"
    "- Kod kusursuzsa: 'KOD_MÜKEMMEL'"
)

# 10. ARAÇ: İZOLE HAFIZALI VE KENDİ KENDİNİ DÜZELTEN SVG ÜRETİCİ
def svg_uret(gorsel_alani, dosya_alt_yolu, tema_ozeti, istek):
    global SVG_OTURUMLARI, RESSAM_TALIMATI, SVG_KRITIK_TALIMATI
    
    if dosya_alt_yolu.startswith("assets/"): dosya_alt_yolu = dosya_alt_yolu[7:]
    if not dosya_alt_yolu.endswith(".svg"): dosya_alt_yolu += ".svg"
            
    tam_yol = os.path.join("assets", dosya_alt_yolu)
    os.makedirs(os.path.dirname(tam_yol), exist_ok=True)

    try:
        # [GÜNCELLEME - YENİ SDK]: .env'den anahtarı alıp yeni nesil Client'ı başlatıyoruz
        
        load_dotenv()
        api_anahtari = os.getenv("GEMINI_API_KEY")
        
        # [GÜNCELLEME - YENİ SDK]: genai.Client nesnesi üzerinden işlem yapıyoruz
        
        client = genai.Client(api_key=api_anahtari)
        
        # KALICI HAFIZA KONTROLÜ: Bu görsel alanı için uzmanlar daha önce açılmadıysa sıfırdan kur
        if gorsel_alani not in SVG_OTURUMLARI:
            # [GÜNCELLEME - YENİ SDK]: start_chat yerine client.chats.create kullanıyoruz
            p_chat = client.chats.create(
                model="gemini-2.5-flash",
                history=[
                    types.Content(role="user", parts=[types.Part.from_text(text=f"SİSTEM: {RESSAM_TALIMATI}")]),
                    types.Content(role="model", parts=[types.Part.from_text(text="Anlaşıldı. Sadece ham SVG kodları yazacağım.")])
                ]
            )
            
            c_chat = client.chats.create(
                model="gemini-2.5-flash",
                history=[
                    types.Content(role="user", parts=[types.Part.from_text(text=f"SİSTEM: {SVG_KRITIK_TALIMATI} Proje Teması: {tema_ozeti}")]),
                    types.Content(role="model", parts=[types.Part.from_text(text="Anlaşıldı. Sadece istenen formatta denetim sonucu vereceğim.")])
                ]
            )
            
            # İkisini de kalıcı hafıza sözlüğüne mühürle
            SVG_OTURUMLARI[gorsel_alani] = {"ressam": p_chat, "kritik": c_chat}
            oturum_durumu = "Yeni uzmanlar başlatıldı."
        else:
            oturum_durumu = "Mevcut görsel alanı hafızasından devam ediliyor."
            
        # Hafızadaki aktif uzmanları çağır
        aktif_ressam = SVG_OTURUMLARI[gorsel_alani]["ressam"]
        aktif_kritik = SVG_OTURUMLARI[gorsel_alani]["kritik"]
        
        maksimum_tur = 3
        son_svg_kodu = ""
        rapor_detayi = ""
        mevcut_istek = istek

        # İçerideki Otonom Çekiç-Örs Döngüsü
        for tur in range(1, maksimum_tur + 1):
            rapor_detayi += f"Tur {tur}: "
            
            # 1. Ressam Çizer (Geçmişini bildiği için düzeltmeleri doğrudan uygular)
            p_resp = zirhli_mesaj_gonder(aktif_ressam, mevcut_istek)
            svg_kodu = p_resp.text.strip()
            
            match = re.search(r'<svg[\s\S]*?</svg>', svg_kodu, re.IGNORECASE)
            if match: svg_kodu = match.group(0)
            
            if not svg_kodu.startswith("<svg"):
                rapor_detayi += "HATA: Geçerli bir <svg> bloğu üretilemedi. "
                break
                
            son_svg_kodu = svg_kodu
            
            # 2. Kritik Denetler
            c_resp = zirhli_mesaj_gonder(aktif_kritik, f"Denetle:\n{svg_kodu}")
            geribildirim = c_resp.text.strip()
            rapor_detayi += f"Kritik: {geribildirim}. "
            
            if "KOD_MÜKEMMEL" in geribildirim:
                break
            else:
                mevcut_istek = geribildirim
                
        if son_svg_kodu.startswith("<svg"):
            with open(tam_yol, "w", encoding="utf-8") as dosya:
                dosya.write(son_svg_kodu)
            return f"BAŞARILI: '{gorsel_alani}' SVG dosyası yazıldı. ({oturum_durumu}) Denetim: {rapor_detayi.strip()}"
        else:
            return f"HATA: 3 denemede SVG üretilemedi. Rapor: {rapor_detayi}"

    except Exception as hata:
        return f"HATA (SVG Aracı - {gorsel_alani}): {hata}"


# Logo alt-ajanının izole hafızasını tutacak global değişken
# --- 3. UZMAN (AKTÖR): LOGO ÇİZER ---
LOGO_RESSAM_TALIMATI = (
    "Sen sadece 'Android Vector Drawable' XML formatında ikonlar tasarlayan dünya standartlarında bir uzmansın. "
    "Kullanıcının isteğine uygun, şık ve renkli bir vektörel ikon kodu üret. Asla markdown (```xml vb.) blokları veya açıklama metni yazma. "
    "Sadece <vector> ile başlayıp </vector> ile biten ham XML kodunu ver. "
    "android:width, android:height, android:viewportWidth ve android:viewportHeight değerlerini mutlaka eksiksiz tanımla."
)

# --- 4. UZMAN (KRİTİK): LOGO DEDETİFİ ---
LOGO_KRITIK_TALIMATI = (
    "Sen dünya standartlarında bir Android Vector XML kodu denetçisi ve görsel kalite kontrol uzmanısın. "
    "Senin görevi, Logo Çizer'in ürettiği XML kodunu ve projenin Tema Özeti'ni analiz etmektir. "
    "Şu 3 noktaya odaklan: \n"
    "1. TEKNİK HATA: <vector>, android:pathData kapatma etiketleri tam mı? Nitelikler (android:fillColor vb.) geçerli mi?\n"
    "2. TEMA UYUMU: İkonun renkleri ve tarzı, verilen Tema Özeti'ndeki tarza uygun mu?\n"
    "3. GÖRÜNÜRLÜK: Uygulama zemini ile ikon renkleri çakışıyor mu?\n"
    "Denetim Sonucunu Sadece Şu İki Formatla Döndür: \n"
    "- Eğer hata bulursan: 'HATA_DENETİMİ: [Net ve teknik hata tanımı ve düzeltme önerisi]'\n"
    "- Eğer kod mükemmelse: 'KOD_MÜKEMMEL'"
)

# 11. ARAÇ: OTONOM ANDROID LOGO ÜRETİCİ VE YERLEŞTİRİCİ (ALT-AJAN)
def android_logosu_uret(istek, tema_ozeti):
    global LOGO_RESSAM_TALIMATI, LOGO_KRITIK_TALIMATI
    
    drawable_dizini = os.path.join("android", "app", "src", "main", "res", "drawable")
    logo_yolu = os.path.join(drawable_dizini, "otonom_logo.xml")
    manifest_yolu = os.path.join("android", "app", "src", "main", "AndroidManifest.xml")
    
    if not os.path.exists(manifest_yolu):
        return "HATA: AndroidManifest.xml dosyası bulunamadı. Tabela güncellenemez."
        
    os.makedirs(drawable_dizini, exist_ok=True)
    
    try:
        # [GÜNCELLEME - YENİ SDK]: .env'den anahtarı alıp yeni nesil Client'ı başlatıyoruz
        
        load_dotenv()
        api_anahtari = os.getenv("GEMINI_API_KEY")
        
        # [GÜNCELLEME - YENİ SDK]: genai.Client nesnesi üzerinden işlem yapıyoruz

        client = genai.Client(api_key=api_anahtari)
        
        # [GÜNCELLEME - YENİ SDK]: İZOLASYON: İki bağımsız chat nesnesini yeni SDK ile açıyoruz
        logo_painter_chat = client.chats.create(
            model="gemini-2.5-flash",
            history=[
                types.Content(role="user", parts=[types.Part.from_text(text=f"SİSTEM: {LOGO_RESSAM_TALIMATI}")]),
                types.Content(role="model", parts=[types.Part.from_text(text="Anlaşıldı. Sadece ham Android Vector XML kodları yazacağım.")])
            ]
        )
        
        logo_critic_chat = client.chats.create(
            model="gemini-2.5-flash",
            history=[
                types.Content(role="user", parts=[types.Part.from_text(text=f"SİSTEM: {LOGO_KRITIK_TALIMATI} Proje Teması: {tema_ozeti}")]),
                types.Content(role="model", parts=[types.Part.from_text(text="Anlaşıldı. XML hatalarını ve tema uyumunu denetleyip sadece istenen formatta cevap vereceğim.")])
            ]
        )
        
        # Otonom Döngü
        maksimum_tur = 3
        son_logo_xml = ""
        rapor_detayi = ""
        mevcut_istek = istek

        for tur in range(1, maksimum_tur + 1):
            rapor_detayi += f"Tur {tur}: "
            
            # --- ADIM 1: Çizer ---
            painter_response = zirhli_mesaj_gonder(logo_painter_chat, mevcut_istek)
            xml_kodu = painter_response.text.strip()
            
            # Gevezelik filtresi
            match = re.search(r'<vector[\s\S]*?</vector>', xml_kodu, re.IGNORECASE)
            if match:
                xml_kodu = match.group(0)
            
            if not xml_kodu.startswith("<vector"):
                rapor_detayi += "HATA: Çizer geçerli bir <vector> XML bloğu üretemedi. "
                break
                
            son_logo_xml = xml_kodu
            
            # --- ADIM 2: Dedektif ---
            critic_response = zirhli_mesaj_gonder(logo_critic_chat, f"Denetle:\n{xml_kodu}")
            critic_feedback = critic_response.text.strip()
            
            rapor_detayi += f"Dedektif: {critic_feedback}. "
            
            # --- ADIM 3: Karar ---
            if "KOD_MÜKEMMEL" in critic_feedback:
                rapor_detayi += "Logo mükemmel bulundu. "
                break
            else:
                mevcut_istek = critic_feedback
                
        # Döngü bittiğinde elimizdeki son kodu kaydet
        if son_logo_xml.startswith("<vector"):
            # 1. ADIM: Logo dosyasını yaz
            with open(logo_yolu, "w", encoding="utf-8") as dosya:
                dosya.write(son_logo_xml)
                
            # 2. ADIM: Manifest tabelasını güncelle (Enjeksiyon)
            with open(manifest_yolu, "r", encoding="utf-8") as dosya:
                manifest_icerik = dosya.read()
                
            # GÜVENLİK: Eski sistemlerde çakışma yapan android:roundIcon="..." tanımını kökünden temizle
            manifest_icerik = re.sub(r'\sandroid:roundIcon="[^"]*"', '', manifest_icerik)
            
            # android:icon="..." değerini bizim yeni vektörel logomuza yönlendir
            manifest_icerik, degisim_sayisi = re.subn(
                r'android:icon="[^"]*"', 
                'android:icon="@drawable/otonom_logo"', 
                manifest_icerik
            )
            
            if degisim_sayisi == 0:
                return "HATA: Manifest içinde 'android:icon' niteliği bulunamadı. Logo dosyası yazıldı ama tabelaya bağlanamadı."
                
            with open(manifest_yolu, "w", encoding="utf-8") as dosya:
                dosya.write(manifest_icerik)
                
            return (
                f"BAŞARILI: Android logosu çizildi, '{logo_yolu}' konumuna yazıldı ve Manifest'e bağlandı. "
                f"Denetim Özeti: ({rapor_detayi.strip()})"
            )
        else:
            return f"HATA: Logo üretimi 3 denemeden sonra bile başarısız oldu. Son Rapor: {rapor_detayi}"
        
    except Exception as hata:
        return f"HATA (Android Logo Alt-Ajanı): {hata}"     
        # Otonom Döngü
        maksimum_tur = 3
        son_logo_xml = ""
        rapor_detayi = ""
        mevcut_istek = istek

        for tur in range(1, maksimum_tur + 1):
            rapor_detayi += f"Tur {tur}: "
            
            # --- ADIM 1: Çizer ---
            painter_response = logo_painter_chat.send_message(mevcut_istek)
            xml_kodu = painter_response.text.strip()
            
            # Gevezelik filtresi
            match = re.search(r'<vector[\s\S]*?</vector>', xml_kodu, re.IGNORECASE)
            if match:
                xml_kodu = match.group(0)
            
            if not xml_kodu.startswith("<vector"):
                rapor_detayi += "HATA: Çizer geçerli bir <vector> XML bloğu üretemedi. "
                break
                
            son_logo_xml = xml_kodu
            
            # --- ADIM 2: Dedektif ---
            critic_response = logo_critic_chat.send_message(f"Denetle:\n{xml_kodu}")
            critic_feedback = critic_response.text.strip()
            
            rapor_detayi += f"Dedektif: {critic_feedback}. "
            
            # --- ADIM 3: Karar ---
            if "KOD_MÜKEMMEL" in critic_feedback:
                rapor_detayi += "Logo mükemmel bulundu. "
                break
            else:
                mevcut_istek = critic_feedback
                
        # Döngü bittiğinde elimizdeki son kodu kaydet
        if son_logo_xml.startswith("<vector"):
            # 1. ADIM: Logo dosyasını yaz
            with open(logo_yolu, "w", encoding="utf-8") as dosya:
                dosya.write(son_logo_xml)
                
            # 2. ADIM: Manifest tabelasını güncelle (Enjeksiyon)
            with open(manifest_yolu, "r", encoding="utf-8") as dosya:
                manifest_icerik = dosya.read()
                
            # GÜVENLİK: Eski sistemlerde çakışma yapan android:roundIcon="..." tanımını kökünden temizle
            manifest_icerik = re.sub(r'\sandroid:roundIcon="[^"]*"', '', manifest_icerik)
            
            # android:icon="..." değerini bizim yeni vektörel logomuza yönlendir
            manifest_icerik, degisim_sayisi = re.subn(
                r'android:icon="[^"]*"', 
                'android:icon="@drawable/otonom_logo"', 
                manifest_icerik
            )
            
            if degisim_sayisi == 0:
                return "HATA: Manifest içinde 'android:icon' niteliği bulunamadı. Logo dosyası yazıldı ama tabelaya bağlanamadı."
                
            with open(manifest_yolu, "w", encoding="utf-8") as dosya:
                dosya.write(manifest_icerik)
                
            return (
                f"BAŞARILI: Android logosu çizildi, '{logo_yolu}' konumuna yazıldı ve Manifest'e bağlandı. "
                f"Denetim Özeti: ({rapor_detayi.strip()})"
            )
        else:
            return f"HATA: Logo üretimi 3 denemeden sonra bile başarısız oldu. Son Rapor: {rapor_detayi}"
        
    except Exception as hata:
        return f"HATA (Android Logo Alt-Ajanı): {hata}"
# 12. ARAÇ: KULLANICIYA SOR / DANIŞ (İNSAN FRENİ)
def kullaniciya_sor(soru):
    """
    Ajanın tıkandığında, tasarım kararı alması gerektiğinde veya emin olamadığında
    kodu duraklatıp terminal üzerinden doğrudan kullanıcıya (insana) soru sormasını sağlar.
    Halüsinasyonu önleyen en kritik kontrol aracıdır.
    """
    # Terminalde belirgin ve dikkat çekici bir formatta soruyu ekrana basıyoruz
    print("\n" + "="*50)
    print(f"🛑 [AJAN SİZE DANIŞIYOR]: {soru}")
    print("="*50)
    
    try:
        # Kod burada durur ve kullanıcının terminale yazı yazıp Enter'a basmasını bekler
        cevap = input("Cevabınız (Talimatı yazıp Enter'a basın): ")
        
        # Alınan cevabı sterilize edip ajanın anlayacağı net bir formatta geri döndürüyoruz
        return f"KULLANICI CEVABI / TALİMATI: {cevap.strip()}"
        
    except Exception as hata:
        return f"HATA (Kullanıcı Girişi Alınamadı): {hata}"
# 13. ARAÇ: GÜVENLİ DOSYA VE BOŞ KLASÖR SİLİCİ
def dosya_sil(dosya_yolu):
    """
    Sadece 'lib/' ve 'assets/' klasörleri altındaki spesifik dosyaları siler.
    Sistem dosyalarına (pubspec.yaml, Manifest vb.) veya kök dizinlere dokunamaz.
    Dosya silindikten sonra geriye kalan boş ebeveyn klasörleri de kökünden temizler.
    """
    # Güvenlik 1: Baştaki/sondaki boşlukları ve ters slashları temizle
    dosya_yolu = dosya_yolu.strip().replace("\\", "/")
    
    # Güvenlik 2: Dizin tırmanma (directory traversal) saldırısını/hatasını önle
    if ".." in dosya_yolu:
        return "HATA: Geçersiz dosya yolu ('..' kullanılarak üst dizinlere geçilemez)."
        
    # Güvenlik 3: Sadece lib/ veya assets/ ile başlayan yollara izin ver
    if not (dosya_yolu.startswith("lib/") or dosya_yolu.startswith("assets/")):
        return "HATA: Güvenlik İhlali! Sadece 'lib/' veya 'assets/' klasörleri altındaki dosyaları silebilirsiniz."
        
    tam_yol = dosya_yolu
    
    # Dosya gerçekten var mı?
    if not os.path.exists(tam_yol):
        return f"BİLGİ: '{tam_yol}' zaten mevcut değil veya daha önce silinmiş."
        
    # Klasör mü dosya mı? (Sadece doğrudan dosyaları hedeflemesini istiyoruz)
    if not os.path.isfile(tam_yol):
        return f"HATA: '{tam_yol}' bir klasördür. Doğrudan klasör silinemez, spesifik bir dosya adı belirtmelisiniz."
        
    try:
        # 1. ADIM: Dosyayı fiziksel olarak sil
        os.remove(tam_yol)
        mesaj = f"BAŞARILI: '{tam_yol}' kalıcı olarak silindi."
        
        # 2. ADIM: Boş kalan klasörleri yukarıya doğru buda (Pruning)
        klasor = os.path.dirname(tam_yol)
        
        # Ana 'lib' veya 'assets' kök klasörlerini silmemesi için güvenli bir döngü sınırı koyuyoruz
        while klasor and klasor not in ["lib", "assets", ".", ""]:
            # Eğer klasörün içi tamamen boşsa
            if not os.listdir(klasor):
                os.rmdir(klasor)
                mesaj += f" Boş kalan '{klasor}/' klasörü de temizlendi."
                # Bir üst klasöre geçip onun da boş kalıp kalmadığını kontrol et
                klasor = os.path.dirname(klasor)
            else:
                # Klasörün içinde başka dosyalar varsa budamayı derhal durdur
                break
                
        return mesaj
        
    except Exception as hata:
        return f"HATA (Dosya Silme): {hata}"



