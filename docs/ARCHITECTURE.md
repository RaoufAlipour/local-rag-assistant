# Mimari ve proje eşlemesi

## Akış

İndeksleme: dosya → metin/sayfa → örtüşen kelime pencereleri → Foundry embedding → normalize vektör → SQLite.

Soru: sorgu embedding'i ve sözcükler → cosine + BM25 → birleşik sıralamada en iyi üç parça → kaynak kimlikli bağlam → Foundry sohbet modeli → kaynak denetimi → cevap.

Varsayılan `hybrid` arama, sıralamaları reciprocal rank fusion ile birleştirir (k=60).
Cosine eşiğini geçen parçalar adaydır. BM25 kolu, uzun sorguda en az iki ayrı sorgu
terimini eşleştiren parçaları eşik altında da aday yapabilir; tek terimli sorguda bir
tam terim eşleşmesi yeterlidir. İki koldan da sıralama alan parça iki katkı alır.
Eşik, BM25 ve birleşik puan birer doğruluk olasılığı değildir. Sözcük örtüşmesi
konu dışı bağlam getirebilir; kapsam dışı sorular da yeni model deneyinde tekrar sınanır.
Türkçe kök bulma yapılmaz. Kod tanımlayıcıları ve tek harfli seçenekler korunur.

`score` cosine olarak kalır; `lexical_score`, `fusion_score`, `matched_terms` eklenir.
`--retrieval-mode semantic` eski yalnız-cosine sıralama/eşik davranışıdır.
Her sorguda saklı metinlerden BM25 hesaplanır; SQLite şeması ve embedding kimliği değişmez.

## Kararlar

- SQLite standart Python kitaplığındandır. Vektörler JSON olarak saklanır ve Python'da karşılaştırılır.
  Küçük veri kümesi için basittir; arama O(N × D) maliyetlidir. Büyük koleksiyon hedeflenmemiştir.
- Dosya SHA-256 özeti ve parçalama ayarları değişmeyen belgeleri tanır. Yeni vektörler tamamen
  hazır olmadan veritabanına yazılmaz. Başarısız okuma/embedding önceki geçerli indeksi korur.
- Model kimliği, gerçek varyant kimliği, SDK sürümü ve sorgu yönergesi sürümünü içerir.
  Sadece vektör boyutunun eşit olması uyumluluk kanıtı kabul edilmez.
- Qwen3 sorgusu görev yönergesi içerir; belge metnine aynı yönerge eklenmez.
- SDK native `EmbeddingsSession` ve `ChatSession` kullanılır. Her soru yeni sohbet session'ıdır.
- Kaynak numaraları uygulama tarafından atanır. Modelin işaret ettiği numaralar getirilen
  parçalarla eşleştirilir. Kaynaksız veya bilinmeyen kaynaklı cevap normal cevap olarak gösterilmez.
- İlk indirmeler açık `prepare` komutundadır. Cevap komutu eksik modeli otomatik indirmez.
- Belgelerin içindeki komutları uygulamama talimatı sistem mesajındadır. Uygulama model
  çıktısını kod olarak çalıştırmaz ve modele araç/işletim sistemi erişimi vermez.

## Sınırlamalar

Kaynak numarasının var olması iddianın kaynakla desteklendiğini kanıtlamaz. Semantik doğruluk,
Türkçe kalite, kapsam dışı sorularda geri çekilme ve prompt injection direnci gerçek modelle
ayrıca değerlendirilecektir. Prompt tek başına garanti sağlamaz.

Kelime pencereleri kod bloklarını veya paragrafları bölebilir. Karmaşık PDF düzenleri kusursuz
çıkarılamaz. OCR ve görsel/tablo anlama kapsam dışıdır. Katalog veya model sürümü değişimi
yeniden indeksleme gerektirebilir. CPU/GPU performansı bu paketin test sürelerinden çıkarılamaz.

Eşik ayarı, model karşılaştırması, gerçek çevrimdışı deneme ve Windows kurulumu tamamlanmadan
“tamamı doğrulanmış çevrimdışı asistan” olarak sunulmamalıdır.

## PDF gereksinimleri

| Gereksinim | Uygulama | Kabul kontrolü |
|---|---|---|
| Foundry kurulum/Hello | `doctor`, `models`, `prepare`, `hello` | Windows'ta gerçek cevap |
| Yerel embedding | `FoundryEmbedder` | Gerçek modelle boyut ve benzerlik |
| SQLite | `Store` | Kayıt, yeniden açma, tekrar indeksleme testleri |
| Belge parçalama | `read_pages`, `split_text` | Metin/sayfa ve örtüşme testleri |
| Top-k arama | `Store.retrieve` | Doğru belgeyi getirme oranı |
| LLM bağlantısı | `FoundryGenerator` | Kaynak destekli Türkçe cevap |
| Arayüz | CLI | Soru, hata, çıkış davranışı |
| Test ve performans | `evaluate` | 14 gerçek cevap için insan değerlendirmesi |
| Dokümantasyon | README ve bu dosya | Temiz Windows kurulumundan tekrar üretim |
| Sunum/canlı demo | Sonraki aşama | Gerçek ölçümlerden sonra hazırlanacak |

## Değerlendirme kayıtları ve çevrimdışı deneme

`evaluate` bütün sonuçları ve deneye ait ayarları tek JSON nesnesinde tutar. Her tamamlanan
soru atomik dosya değişimiyle kaydedilir. Model/indeks/kod/soru özeti farklıysa `--resume`
sonuçları birleştirmez. Bu kontrol semantik doğruluk puanlaması yapmaz.

`answered`: kaynak etiketi geçerli; doğruluk ayrıca incelenir.
`model_abstained`: modelin geri çekilme cevabı (sonuna kaynak etiketi eklese de).
`conflicting_answer`: cevapla birlikte geri çekilme ifadesi üretilmiş; normal cevap olarak sunulmaz.
`invalid_citations`: eksik/geçersiz kaynak numarası; kaynak metinleri incelemeye sunulur.
`no_context`: seçilen arama modunun aday koşullarını sağlayan kaynak yok; sohbet modeli çağrılmaz.

`prepare` kamuya açık model adını gerçek varyant kimliğiyle `storage/model-map.json`
dosyasında eşler. Önbellek kaydının görev bilgisi eksikse bu kayıt inference'a verilmez.
SDK 2.0.1'in bu Linux ortamındaki ağ engelli başlangıcında katalog metadata sorunu görüldü:
model dosyaları bulunmasına rağmen `task=None` dönebiliyor. Bu aşamada ağsız inference
kabulü başarılı değildir; model eşleme dosyası tek başına bu SDK sorununu çözmez.

Linux deneme aracı SDK importundan önce seccomp filtresi yükler; socket oluşturma,
connect/send ve io_uring_setup çağrılarını engeller. IPv4/IPv6 TCP/UDP kontrolü EPERM
bekler; engel yüklenmezse CLI çalıştırılmaz. Bu bir süreç testi ve hata yeniden üretim
aracıdır; Windows sonucu veya tüm platformlar için güvenlik sertifikası değildir.

## Süreç başına CUDA kaydı

Windows kullanıcı deneyi EP kaydının yeni süreçte yeniden gerektiğini gösterdi.
Runtime seçilen cihazı prepare tarafından kaydedilen ayardan veya --device seçeneğinden alır;
CUDA EP'sini aynı süreçte kaydettikten sonra model varyantını seçer. Başarısız kayıt veya
CUDA varyantının yokluğu hata üretir. CPU/CUDA embedding kimlikleri farklı kalır.
Model ağırlığı indirme yalnız prepare komutundadır; EP hazırlama/kayıt API'si açılışta
kullanıldığından ağ erişimi yapabilir. Çevrimdışı kabul testi bu yolu da kapsar.

## İsteğe bağlı yerel katalog

Windows soğuk başlangıç testi de metadata eksikliğiyle başarısız oldu.
Yeni `snapshot` komutu iki seçili modelin SDK ModelInfo kaydını atomik saklar.
`--offline` açıkça seçilince salt okunur HTTP metadata servisi yalnız 127.0.0.1'in
dinamik portuna bağlanır; SDK catalog_urls bu gerçek yerel servise yöneltilir.
Bu servis model ağırlıkları, belgeler veya cevapları HTTP üzerinden sunmaz.
Snapshot'ın SDK sürümü, cihazı, model kimliği, görev/sağlayıcı alanları ve özeti doğrulanır.
Özet kazara değişikliği yakalar; imza veya kimlik doğrulama değildir.
Katalog modu değerlendirme kaydına girer. Çekirdek arama/yönerge değişmedi.
EP kaydı ve native SDK tanılama girişimleri --offline tarafından engellenmez;
gerçek internet kesintisi altında kabul testi hâlâ gerekir. Tam ağ engeli değildir.
