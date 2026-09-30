# Windows CUDA kalite v3 — kaynak seçimi incelemesi

Kullanıcının internet kapalı çalıştırdığını bildirdiği 24 soruluk deney incelendi.
Ham çıktı docs/evidence/windows-cuda-quality-v3.json; özgün veri değiştirilmedi.
CUDA modelleri, yerel katalog, hybrid arama ve extractive cevap modu kayıtlıdır.

| Kontrol | Sonuç |
|---|---|
| Tamamlanan soru | 24/24 |
| Cevaplanabilir soruda doğru kaynak | 17/17 |
| Kaynak incelemesine göre yeterli cevap | 16/17 |
| Eksik ayrıntı | 1/17: 6. soruda print'in None dönüşü yok |
| Ham kayıtta uygun ret durumu | 5/7 |
| Ham kayıtta ret biçimi hatası | 2/7: 11 ve 24, model çıktısı boş JSON listesi |
| Düzeltilmiş ayrıştırıcıyla aynı kayıtların tekrarı | 7/7 uygun ret; 17 cevabın metni aynı |

## Cevap kalitesi

break–continue cevabı artık en içteki döngü ve mevcut turun kalanı ayrımını
eksiksiz aktarıyor. raise ValueError–return ValueError ayrımında sınıfın
sıradan dönüş değeri olması açıkça belirtiliyor. print–return karşılaştırması
yanlış bilgi üretmiyor; ancak bu soru için önceden belirlenen katı rubrikteki
None ayrıntısını seçmedi. Doğrudan “print fonksiyonunun dönüş değeri nedir?”
sorusunda ise None doğru aktarıldı. Bu nedenle bütün 17 cevabı tam başarılı
ilan etmiyoruz. 2 ve 19. sorularda doğru ama gereksiz ek alıntılar da var.

Her cevap kaynak cümlesinin aynısıdır. Bu özellik tek başına soru ile ilgililiği,
eksiksizliği veya belgenin doğruluğunu kanıtlamaz. Ayrı vaka değerlendirmeleri
docs/evidence/windows-cuda-quality-v3-review.json içindedir. İnceleme asistan
tarafından yapılmıştır; bağımsız kör test değildir.

## İki biçim hatasının düzeltmesi

Model 11 ve 24. sorularda {"selections":[]} yerine [] üretmiş. Yeni parser
yalnız boş üst düzey JSON listesini boş seçim olarak kabul eder. Dolu listeler,
ek açıklamalar, fazladan alanlar ve geçersiz kimlikler hâlâ reddedilir. Prompt
ve model üretimi değiştirilmedi. Ham model çıktısı her zaman korunur.

Kayıtlı 24 sonuç yeni kodla tekrar işlendi. Yalnız iki durum ve bunların kullanıcıya
gösterilen ret metni değişti; diğer 22 cevap aynı kaldı. Bu yeni bir GPU çıkarımı
veya yeni hız ölçümü değildir. Kanıt: docs/evidence/windows-cuda-quality-v3-replay.json.
Tekrarlanabilir komut (farklı bir çıktı yolu kullanın):

    python scripts/replay_evidence.py docs/evidence/windows-cuda-quality-v3.json storage/quality-v3-replay.json

## Süreler ve kalan sınırlar

Toplam 341,91 saniye; tüm soruların ortalaması 14,246 saniye. İlk soruda model
yükleme 3,932 saniye ve SDK yanıt çağrısı 26,197 saniye. Sonraki 19 model
çağrısında model yükleme 0 saniye; SDK yanıt çağrısı ortalama 16,202 saniye.
Katalog/oturum maliyetleri küçük. SDK çağrısı içindeki zamanın ne kadarının
hesaplama veya bekleme olduğu bu ölçümle ayrıştırılamıyor. Gecikmenin kök nedeni
belirlenmedi; arayüz eklenmesi hız düzeltmesi olarak sunulmamalıdır.

Bu sonuçlar arayüz geliştirmesine geçmek için yeterli bir çalışan örnek sağlıyor.
Tam kalite kabulü açık: karşılaştırma cevabındaki eksik ayrıntı, gereksiz alıntılar,
geliştirmede kullanılmamış sorular ve daha uzun belgeler ayrıca değerlendirilmeli.
Kullanıcıdan aynı 24 soruluk GPU deneyini tekrar etmesi istenmiyor.

