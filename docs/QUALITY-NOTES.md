# Gerçek model kalite incelemeleri

## Çevrimdışı Windows sonucu — 12 Eylül 2026

14/14 tamamlandı: 9/9 kaynak, 5/5 kapsam dışı ret. Bütün ham model yanıtları v2 ile
aynı; 6 uygun cevap ve 3 düzeltme gerektiren cevap değerlendirmesi değişmedi.
İşlevsel çevrimdışı kontrol başarılı; son kalite kabulü ve gecikme incelemesi açık.
Kaynak: `WINDOWS-OFFLINE-REVIEW.md`.

## Güncel Windows sonucu — 11 Eylül 2026

V2 hybrid deneyi incelendi: 9/9 doğru kaynak, 5/5 uygun ret; 6 uygun cevap, 3 düzeltme
gerektiren cevap. `w` yanlışı düzeldi; `return ValueError` açıklaması iyileşti ancak
kesinleştirilmeli. `print` için “değer döndürmez” teknik yanlışı var (None döndürür).
Güncel rapor `WINDOWS-CUDA-REVIEW-V2.md`. Kod bu incelemede değiştirilmedi; sıradaki
ayrı kontrol Windows ağsız soğuk başlangıçtır. Kalite kabulü açık kalır.

### İlk Windows deneyinin kaydı

CUDA Qwen2.5 7B değerlendirmesi 14/14 tamamlandı. İki gerçek bilgi hatası ve iki
hassasiyet/terim sorunu bulundu. Kapsam dışı ham davranış 5/5 ret; eski ayrıştırıcı
virgülle ayrılmış kaynakları olan bir reti yanlışlıkla çelişkili saymış.
Tam kaynak incelemesi `WINDOWS-CUDA-REVIEW.md` içindedir. Yeni hybrid arama ve yönerge
yerel regresyon testlerinden geçti; gerçek modelle yeniden kalite ölçümü bekleniyor.
Aşağıdaki Linux sonuçları önceki deneylerdir; güncel Windows sonucu yerine kullanılmaz.

## Kaydedilmiş ilk deneyler

0.5B model `break` / `continue` ayrımını yanlış açıkladı ve kaynak etiketi vermedi.
Ham kayıt: `docs/evidence/baseline-0.5b.json`. Bu tek örnek genel bir benchmark değildir.

1.5B denemesinden **14 sorunun yalnız ilk 7 sonucu** kalmıştır. Bu tamamlanmış bir
14 soruluk değerlendirme değildir. Ham kayıt değiştirilmedi: `docs/evidence/evaluation-1.5b.json`.
Aşağıdaki değerlendirme Codex'in kaynaklarla karşılaştırmasıdır; kullanıcı/öğretmen onayı değildir.

| Soru | Uygulama durumu | İnceleme | Gerekçe |
|---|---|---|---|
| input() hangi veri türünü döndürür? | answered | Kısmen uygun | str doğru; yanıt üç kısa cümle sınırını aşıyor. |
| Atama ve eşitlik operatörlerinin farkı nedir? | invalid_citations | Başarısız | Atama/eşitlik farkı açık değil, tekrarlar ve geçersiz kaynak biçimi var. |
| range(5) hangi sayıları üretir? | invalid_citations | Başarısız | 0–4 doğru; istenen kaynak etiketi yok. |
| break ile continue farkı nedir? | model_abstained | Başarısız | Kaynakta açık cevap varken geri çekildi. |
| Fonksiyonun dışında return yazarsam ne olur? | model_abstained | Başarısız | SyntaxError kaynakta var, model geri çekildi. |
| print ile return aynı şey mi? | model_abstained | Başarısız | print/return farkı kaynakta var, model geri çekildi. |
| Bir metni nasıl ters çeviririm? | answered | Başarısız | Metni ters çevirmek yerine sözlüklerden bahsediyor; geçerli [S1] etiketi bunu doğru yapmıyor. |

Doğru belge bu 7 sorunun hepsinde ilk sıradadır. Kaynak araması ile cevap üretimi ayrı
ölçülmelidir. `answered` sadece kaynak numarası biçiminin geçerli olduğunu söyler;
cevabın doğru veya ilgili olduğunu söylemez. İki `answered` kaydından biri konu dışı cevaptır.
Kapsam dışı beş sorunun hiçbiri bu eski kayıtta çalıştırılmamıştır.

Kaydedilen ortalama soru süresi 16,455 saniyedir; bu eski Linux sürecinde ölçülen
retrieval + generation süresidir. Programın açılışı ve embedding model yüklemesi dahil değildir;
sohbet modelinin ilk yüklemesi ilk generation süresine dahil olabilir. Windows hız tahmini değildir.

## Yapılan düzeltmeler

- Native MessageItem/TextItem cevap yapısı okunuyor; iki SDK regresyon testi vardır.
- Değerlendirme her soru sonrasında atomik kaydedilir. Kesintide son tamamlanan sonuç korunur.
- `--resume` aynı deneye devam eder. Kod, gerçek model kimliği, indeks veya soru değişirse reddeder.
- Var olan sonuç dosyası sessizce ezilmez; yeni deney farklı `--output` ister.
- `report` model yüklemeden ham kayıtların özetini verir. Semantik başarı oranı uydurmaz.

## Kabul için kalan kontroller

Dokuz cevaplanabilir soruda doğruluk/kaynak desteği; beş kapsam dışı soruda geri çekilme;
soğuk başlangıçtan çevrimdışı soru-cevap; kullanıcı Windows cihazında kurulum ve hız.
Model büyütmek veya top-k düşürmek tek başına başarı kanıtı değildir; değişiklikler tekrar ölçülmelidir.

## Tamamlanan 1.5B / top-k=1 deneyi

`docs/evidence/evaluation-current-top1.json`: 14/14 soru tamamlandı, threshold=0.35.
Bu deney, çelişkili cevap ve kaynak etiketli ret sınıflandırması düzeltilmeden önce başladı;
ham durum alanları değiştirilmedi. Sorunlu sınıflandırmalar aşağıdaki içerik incelemesinde ayrıldı.

- Dokuz cevaplanabilir sorudan sekizinde beklenen belge getirildi.
- Yalnız `range(5)` sorusu doğru ve kaynaklı cevap aldı: cevaplanabilir sorularda 1/9.
- `input` yanıtı uygunsuz ret ve kaynak biçimi içeriyor.
- Atama/eşitlik yanıtı belirsiz ve kendi içinde çelişkili.
- `break`, `print/return`, metin ters çevirme ve `raise/return` sorularında kaynak etiketli ret var.
- Fonksiyon dışında return sorusu yanlış ret aldı.
- `w` modu sorusunda doğru belge top-1 dışında kaldı; model ret verdi.
- Kapsam dışı soruların beşinde de uygun geri çekilme var: 5/5.
- Bu küçük geliştirme setinde toplam uygun davranış 6/14; genel model benchmark'ı değildir.
- Ortalama kayıtlı retrieval+generation süresi 12,513 saniye; soğuk program açılışı hariçtir.

Bu sonuç 1.5B modelin nihai model olarak kabul edilmediğini gösterir. Tek kaynak kullanmak
bazı çıktıları kısaltsa da doğruluğu yeterli hale getirmedi.

## 7B ve çevrimdışı son durum

7B modeli indirildi; fakat ilk cevap üretilmeden ortamın toplam bellek tüketimi
14 GiB sınırına dayandı. Deneme durduruldu; 0/14 sonuçtur, kalite/hız sonucu değildir.
`docs/evidence/review-7b-resource.json` bellek gözleminin kapsamını belirtir.

Ağ engelli Linux soğuk başlangıç testi katalog görevi metadata'sı bulunamadığı için
başarısızdır. `docs/evidence/offline-ask-retry.log` gerçek hata kaydıdır. Ağ engelinin
çalışması ile modelin çevrimdışı çalışması birbirinden farklı kontrollerdir.
