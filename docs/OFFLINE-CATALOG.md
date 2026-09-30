# Çevrimdışı katalog sorunu ve çözüm adayı

12 Eylül güncellemesi: Windows CUDA tek soru ve 14 soruluk çevrimdışı değerlendirme
tamamlandı. Sonuçların tamamı çevrimiçi v2 ile aynı; bazı generation süreleri uzadı.
Güncel sonuç `WINDOWS-OFFLINE-REVIEW.md` içindedir. Aşağıdaki “henüz doğrulanmadı”
ifadeleri çözümün teslim edildiği aşamaya ait tarihsel test sınırlarını belirtir.

## Gözlenen hata

Kullanıcı Windows üzerinde interneti kapatıp yeni ask süreci başlattı. Region detection
ve yedi bölge için transport failure uyarılarından sonra qwen3-embedding-0.6b için
tam katalog bilgisi bulunamadı. Cevap üretilmedi. Bu kayıt çevrimdışı kabul başarısızlığıdır.
Aynı cihazda modellerin cached=true ve CUDA ile çalıştığı önceki çevrimiçi kayıtlarda doğrulandı.

SDK 2.0.1 Python EmbeddingsSession ve ChatSession, modelin task alanını kontrol eder.
Bu kontrolü atlamak veya görev bilgisini model adından tahmin etmek çözüm olarak kullanılmadı.
Üretim model nesneleri SDK kataloğundan gelir; private native handle veya SDK kaynak kodu değiştirilmedi.

## Yeni yol

1. İnternet açıkken `snapshot` iki seçili, indirilmiş modelin gerçek SDK ModelInfo verisini kaydeder.
2. Snapshot, sürüm/cihaz/kimlik/görev/sağlayıcı alanları ve içerik özetiyle doğrulanır.
3. `--offline` seçilince yalnız 127.0.0.1 üzerinde geçici, salt okunur katalog açılır.
4. Desteklenen Configuration.catalog_urls seçeneği bu katalog adresini kullanır.
5. SDK gerçek katalog ayrıştırıcısıyla metadata'yı okuyup mevcut ağırlıkları yükler.

`catalog_region` açıkça verilerek otomatik bölge tespitine gerek bırakılmaz; katalog
URL'si cihaz içindedir. Bu değer Azure'a bağlanıldığı anlamına gelmez. Yerel servis
katalog filtrelerini model kimliği, ad, alias, cihaz ve sağlayıcıya göre uygular.
Snapshot komutu ağırlık indirmez ve çıkarım yapmaz. Var olan varsayılan çevrimiçi yol korunur.

Aktarıcı, Python ModelInfo tarafından sunulan ve bu projenin kullandığı SDK 2.0.1
alanlarını katalog yanıt biçimine çevirir. Python API'si bazı gelişmiş alanları
(model_settings ve eski prompt_template gibi) doldurmaz. Bu nedenle her model türü
ve her SDK sürümü için genel katalog kopyalama desteği iddia edilmez; gerçek Qwen
cevapları ve kaynak sadakati yeni Windows denemesinde tekrar değerlendirilmelidir.

## Doğrulama

- 50/50 altyapı ve SDK testi geçti: `docs/test-results-offline-catalog.txt`.
- Native SDK 2.0.1 gerçek katalog ayrıştırıcısı yerel HTTP yanıtını okuyarak doğru
  model kimliği, embeddings görevi ve CPUExecutionProvider döndürdü.
- Bu son test yalnız test metadata'sı kullandı; ağırlık indirmedi/yüklemedi, gerçek cevap üretmedi.
- Tekrar üretim: `python scripts/check_local_catalog_sdk.py`.
- Kayıt: `docs/evidence/local-catalog-sdk-check.txt`.
- Windows CUDA çevrimdışı çıkarımı henüz doğrulanmadı.

Test ortamında eski ONNX Runtime kopyası yüklenirken Bus error verdi; sorun uygulama
kodu çalışmadan önce ctypes.CDLL aşamasındaydı. İzole test dizinine aynı 1.28.0 sürümü
kurulunca native katalog testi geçti. Kullanıcının Windows ortamında paket değişikliği istenmiyor.

## Sınırlar

--offline bir güvenlik duvarı değildir; CUDA EP kayıt API'si veya SDK tanılama kodu
bağlantı girişimi yapabilir. Kullanıcı Wi-Fi/Ethernet kapalıyken yeni süreç başlatıp
hem açılışı hem gerçek cevabı sınamalıdır. Yerel HTTP katalog dış adreslere istek göndermez.
Belge/cevap/ağırlık bu servis üzerinden aktarılmaz. Model indirme yalnız prepare yolunda kalır.

## İncelenen birincil kaynaklar

- Kurulu foundry-local-sdk 2.0.1: configuration.py, catalog.py, imodel.py, session.py.
- [Microsoft SDK Configuration](https://github.com/microsoft/Foundry-Local/blob/main/sdk_v2/python/src/foundry_local_sdk/configuration.py): catalog_urls seçeneği.
- [Microsoft katalog istemcisi](https://github.com/microsoft/Foundry-Local/blob/main/sdk_v2/cpp/src/catalog/azure_catalog_client.cc): özel URL ve yanıt alma yolu.
- [Microsoft katalog yanıt şeması](https://github.com/microsoft/Foundry-Local/blob/main/sdk_v2/cpp/src/catalog/azure_catalog_models.cc): görev, varyant ve metadata ayrıştırması.

GitHub main kaynakları yayımlanan paketten farklı olabileceği için gerçek SDK 2.0.1
ile ayrıştırma testi ayrıca çalıştırıldı. Sonuç, Windows GPU kabulü yerine geçmez.
