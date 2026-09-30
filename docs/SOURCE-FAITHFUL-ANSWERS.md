# Kaynak cümlelerinden cevap — kalite aşaması

**Güncelleme:** aşağıdaki ilk deneme tamamlandı; tekrar çalıştırmak gerekmiyor.
Sonuçlar `docs/WINDOWS-QUALITY-V3-REVIEW.md` içinde. 16/17 cevap yeterli;
bir karşılaştırmada None ayrıntısı eksik. Boş üst düzey JSON listesi de artık
ret kabul edilir; kayıtlı çıktılarla 7/7 ret doğrulandı. Arayüz için sıradaki
komutlar `docs/START-HERE-WINDOWS.md` içindedir. Aşağısı ilk tasarım/deneme kaydıdır.

## Neden eklendi?

Windows çevrimdışı deneyinde arama 9/9 doğru kaynağı buldu. Ancak serbest açıklama
modunda üç cevap yeterince sadık değildi: print'in None dönüşü yanlış anlatıldı;
break/continue kapsamı ve return ValueError sınıfı ayrımı eksik aktarıldı.
Sadece geçerli [S1] etiketi görmek, bu hataları yakalamıyor.

Yeni `--answer-mode extractive` seçeneğinde model, bulunan kaynakların numaralanmış
cümlelerinden en fazla altısını JSON ile seçer. Uygulama sadece geçerli kimlikleri
kabul eder ve cevap metnini SQLite'taki cümlelerden aynen oluşturur. Modelin
yeni yazdığı açıklama, son cevaba eklenmez. Cümleler kaynak sırasıyla gösterilir.
Boş seçim `model_abstained`; bozuk JSON, bilinmeyen/tekrarlanan kimlik, fazla seçim
ve ek alanlar `invalid_evidence` olur. Ham model çıktısı raporda korunur.

Bu bir alıntı seçimi modudur. Modelin kendi ifadeleriyle açıklama yaptığı önceki
mod `--answer-mode generative` olarak korunur ve hâlâ varsayılandır. Yeni mod,
gerçek model değerlendirmesi tamamlanmadan kalite onaylı varsayılan ilan edilmez.

## Neyi garanti eder, neyi etmez?

- `evidence_validation: exact_source`: gösterilen metin, seçilmiş kaynak
  cümlesinin aynısıdır. Kaynak metninin doğruluğunu onaylamaz.
- Model ilgisiz veya eksik cümleler seçebilir. Bu yüzden `answered` hâlâ
  anlamsal doğruluk veya yeterlilik onayı değildir.
- Noktalama ve boşlukla ayrılan cümleler kullanılır. Kelime penceresiyle
  parçalanmış uzun belgelerde cümleler parça sınırında kesilebilir; bu mod
  eksik bağlamı yeniden oluşturmaz. Mevcut altı kısa not tek parça/belgedir.
- Serbest açıklama ve alıntı modları farklı cevap türleridir. Süre ve doğruluk
  karşılaştırmalarında bu fark raporda belirtilmelidir.

## Windows'ta sıradaki tek deneme

ZIP içindeki güncel dosyaları mevcut proje klasörüne kopyalayıp aynı adlı kod
dosyalarını değiştirin. Klasörü silmeyin. Yeni bağımlılık, model indirme,
indeksleme veya snapshot gerekmez; mevcut `.venv` ve `storage` kullanılabilir.

```powershell
.\.venv\Scripts\python.exe main.py evaluate --chat-model qwen2.5-7b --device cuda --offline --retrieval-mode hybrid --answer-mode extractive --cases data/evaluation-quality.json --output storage/windows-cuda-quality-v3.json
```

`--offline` yerel katalog kullanır. Ağsız çalışma denemesini tekrarlamak isterseniz
bağlantıları kapatın; bu bayrak tek başına işletim sistemi ağ engeli oluşturmaz.
İşlem kesilirse aynı komuta `--resume` eklenebilir. Eski deney dosyasının üzerine
yazılmaz; kod/soru/indeks değişmişse devam isteği reddedilir.

24 soru: önceki 14 soru + 10 ek kontrol. Toplam 17 cevaplanabilir, 7 kapsam dışı
soru vardır. Önceki belirsiz beklenen cevaplar yeni dosyada ayrıntılandırılmıştır;
orijinal `evaluation.json` ve ham deney kayıtları değiştirilmemiştir.
Yeni liste geliştirme sırasında hazırlanmış bir regresyon/kapsam genişletme
setidir; bağımsız veya kör test olarak sunulmamalıdır.

Üretilen `storage/windows-cuda-quality-v3.json` dosyası incelenirken:

1. Önceki üç sorun: iki tarafın tanımı ve gerekli niteleyiciler eksiksiz mi?
2. Diğer cevaplar: seçilen alıntılar soruyu gerçekten cevaplıyor mu?
3. Kapsam dışı sorular: uygun ret mi, ilgisiz cümle seçimi mi?
4. Biçim: `invalid_evidence` var mı? Varsa ham JSON ve kaynak kimlikleri incelenir.
5. Süre: ilk soru ve sonraki sorular ayrı değerlendirilir.

Hedef bu sette 17/17 yeterli kaynak cevabı ve 7/7 uygun rettir; sonuç henüz
ölçülmedi. Genel kalite iddiası için ayrıca bu geliştirmede kullanılmamış soru
ve daha uzun belgelerle bağımsız değerlendirme gerekir. Bu aşama kabul edilince
yerel arayüze, ardından rapor ve sunuma geçilir.

## Burada tamamlanan doğrulama

60 altyapı/SDK testi geçti (`docs/test-results-evidence.txt`). Ek sekiz test;
kaynak metnini aynen koruma, sahte kimlik/ek iddia reddi, JSON belirsizliği,
kapsam dışı boş seçim ve kaynak yokken model çağrılmamasını kapsar.
Bu testlerde yeni seçim modunun gerçek Qwen çıktısı kullanılmadı. Windows
kalite ve hız sonucu kullanıcı cihazındaki deneyden sonra eklenecektir.
