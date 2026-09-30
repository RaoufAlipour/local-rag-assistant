# Yerel arayüz

Arayüz hazır: sohbet, kaynak parçalarının tamamını açma, TXT/Markdown/metinli PDF
yükleme, klasörde değişen belgeleri indeksleme, belge sayıları ve oturumu JSON
olarak indirme. Tarayıcıda http://127.0.0.1:8501 üzerinde açılır.

## Mevcut Windows kurulumunda

Güncel ZIP'in içindeki dosyaları mevcut proje klasörüne kopyalayın. .venv,
storage ve kendi belgelerinizi koruyun. Arayüz bağımlılığını **internet açıkken**
bir kez kurun:

    .\.venv\Scripts\python.exe -m pip install -r requirements-ui.txt

Sonra interneti kapatıp arayüzü açabilirsiniz:

    .\.venv\Scripts\python.exe ui.py

Tarayıcı kendiliğinden açılmazsa http://127.0.0.1:8501 adresini açın. PowerShell
penceresi açık kalmalıdır; durdurmak için Ctrl+C kullanın. Yeni model indirme,
snapshot veya mevcut altı notu yeniden indeksleme gerekmez.

Arayüz daima mevcut yerel katalogla çalışır. Kaydedilmiş cihaz ayarı kullanılır
(bu bilgisayarda CUDA). Qwen2.5 7B ve Qwen3 embedding 0.6B mevcut modelleri seçilir.
Arayüzde katalog indirme veya çevrimiçi kataloğa otomatik geri dönüş yoktur.
Bu, işletim sistemi ağ engeli anlamına gelmez; SDK'nın olası tanılama girişimleri
için mevcut offline açıklamaları geçerlidir.

## İlk kullanım kontrolü

1. Sohbet ekranında 6 belge göründüğünü kontrol edin.
2. “break ile continue farkı nedir?” sorusunu sorun.
3. “Kaynakları ve tam bağlamı incele” bölümünde döngüler notunu açın.
4. Belgeler bölümünde mevcut notları görüntüleyin.

Ekran görüntüsü ve varsa hata çıktısı Windows arayüz denemesini tamamlamak için
yeterlidir; yeniden 24 soruluk değerlendirme gerekmez. Yeni belge eklemek
isterseniz önce farklı adlı küçük bir TXT ile deneyebilirsiniz.

## Davranış ve sınırlar

- Varsayılan arayüz cevap biçimi kaynak cümleleridir. CLI varsayılanı eski
  generative mod olarak korunur. Her sonucun modu kendi JSON'unda saklanır.
- SDK işleri tek işçide sırayla yürür. Sayfa etkileşimleri modeli yeniden
  başlatmaz; eşzamanlı sekmelerin model/indeks işleri sıraya girer.
- Sohbet görüntüsü oturumda tutulur. Önceki sorular sonraki modele gönderilmez.
  Sayfayı yenilemek oturumu kaybettirebilir; JSON indirerek saklayabilirsiniz.
- Cevaplar ve belgeler HTML/Markdown olarak çalıştırılmadan düz metin gösterilir.
- Dosya başına 20 MB sınırı vardır. Taranmış PDF için OCR yoktur. Aynı adlı dosya
  yükleme eski dosyayı değiştirmez. Başarısız eklemede yeni dosyalar geri alınır;
  SQLite ingest işlemi önceki veriyi korur.
- Klasörü yeniden taramak yeni/değişmiş belgeleri işler. Klasörden dosya silmek
  indeks kaydını silmez; belge silme arayüzü bu sürümde yoktur.
- Kaynak seçimi eksik olabilir; kaynakların tamamı açılabilir. Açık kalite
  sorunları docs/WINDOWS-QUALITY-V3-REVIEW.md içinde izlenir.
- Hız iyileştirmesi yapılmadı. Son Windows deneyindeki gecikmeler devam edebilir.

## Doğrulama

69 test geçti: altyapı ve SDK testleri, boş JSON listesi regresyonu, dört belge
servisi testi ve dört Streamlit AppTest akış testi. Arayüz testlerinde model
yerine test nesnesi kullanıldı. Dosya hatasında geri alma ve tek işçide yürütme
gerçek dosya/SQLite işlemleriyle kontrol edildi. AppTest; sohbet, kaynak metni,
geçmiş temizleme, belge sayfası, eksik indeks ve hata gösterimini sınadı.
Linux sunucusu için HTTP açılış denemesi ayrıca kaydedildi.
Windows'ta gerçek GPU + arayüz akışı ve tarayıcı görünümü henüz doğrulanmadı.

Streamlit 1.63.0 kullanılır. Kaynak nesnesinin yeniden kullanımı ve AppTest
yöntemi için [önbellek belgeleri](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_resource)
ve [AppTest belgeleri](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest)
esas alındı. Başlatıcı, [yapılandırma seçenekleriyle](https://docs.streamlit.io/develop/api-reference/configuration/config.toml)
sunucuyu loopback'e bağlar ve Streamlit kullanım istatistiğini kapatır.

