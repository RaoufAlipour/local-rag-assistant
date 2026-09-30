# Windows CUDA süre profili — 12 Eylül 2026

İlk sorunun toplam süresi **27.7836 saniye**. Bunun
**4.3597 saniyesi model yükleme**, **23.1608 saniyesi
SDK yanıt çağrısı**. Sonraki dört sorunun ortalaması **2.9609 saniye**;
aralık 1.7173–3.5465 saniye.

## Ölçümlerin gösterdiği

- Sonraki dört soruda model_load_seconds sıfır: bu kayıtta model her soruda yeniden yüklenmiyor.
- Katalog sorguları 0,000149–0,000158 saniye; oturum açma ve kapatma bir milisaniyenin altında.
- Bu kayıttaki baskın süre SDK process_request/response açılış çağrısında.
- response_open_seconds; olası ilk çalıştırma hazırlığını, üretimi ve native beklemeleri
  birlikte içerir. Tamamını GPU hesaplaması veya kesin bir ısınma maliyeti sayamayız.
- Önceki 14 soruluk denemede aralıklı görülen uzun beklemeler sonraki dört soruda
  tekrarlanmadı. Önceki gecikmelerin kök nedeni belirlenmedi; hız sorunu çözüldü denmedi.
- Ölçüm eklemek performans düzeltmesi değildir. Kod bu inceleme sırasında değiştirilmedi.

## Soru bazında süreler

| No | Soru | Model yükleme (sn) | SDK yanıt çağrısı (sn) | Arama (sn) | Toplam (sn) |
|---|---|---:|---:|---:|---:|
| 1 | input() hangi veri türünü döndürür? | 4.3597 | 23.1608 | 0.2612 | 27.7836 |
| 2 | Atama ve eşitlik operatörlerinin farkı nedir? | 0.0000 | 3.5209 | 0.0249 | 3.5465 |
| 3 | range(5) hangi sayıları üretir? | 0.0000 | 2.7698 | 0.3227 | 3.0932 |
| 4 | break ile continue farkı nedir? | 0.0000 | 3.1715 | 0.3144 | 3.4866 |
| 5 | Fonksiyonun dışında return yazarsam ne olur? | 0.0000 | 1.6489 | 0.0676 | 1.7173 |

Model yükleme, model_lookup_and_load_seconds toplamının alt kalemidir; çift sayılmamalıdır.
Program açılışı ve ilk embedding modeli yüklemesi bu ölçümlerin dışındadır.

## Kalite ve kapsam

Beş model cevabı önceki çevrimdışı kaydın ilk beş cevabıyla birebir aynı. Dört
uygun örnek korunmuş; break/continue cevabında en içteki döngü ve mevcut turun kalanına
ilişkin hassasiyet sorunu sürüyor. Bu beş soru print/return sorununu veya kapsam dışı
soruları içermediği için yeni bir tam kalite kabulü değildir.

Tam 14 soruluk sonuç: kaynak 9/9, kapsam dışı ret 5/5, kaynak incelemesinde 6 uygun
cevap ve 3 düzeltme gerektiren cevap. Ayrıntılar `WINDOWS-OFFLINE-REVIEW.md` içindedir.
Gecikme tekrar görülürse mevcut generation_details ölçümü üzerinden incelenebilir.
Sıradaki geliştirme konusu kaynak sadakati; arayüz ve teslim hazırlığı da açık kalır.

## Kullanım ve kanıt

Mevcut chat komutu aynı süreçte soruları alır ve yüklenen modeli kullanmaya devam eder;
sorular için ayrı oturum açılması konuşma hafızası sağlamaz. Yeni ask süreci ise
modeli yeniden yükler. İlk yanıt maliyeti kullanıcıya ilk istekte yansır.

Ham kayıt `docs/evidence/windows-cuda-profile.json` içinde değiştirilmeden saklandı.
Ayrı inceleme `docs/evidence/windows-cuda-profile-review.json` içinde.
SHA-256: `6021a2cbd4a10313211a947ab3c096fdb6d5a42068b98a821549dacac4f34736`.
Kod özeti gönderilmiş v8 koduyla, indeks özeti önceki çevrimdışı deneyle eşleşti.
