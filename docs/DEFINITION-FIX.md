# Kısa tanım sorularında ilgisiz alıntı düzeltmesi — 14 Eylül 2026

Kullanıcının arayüzden dışa aktardığı "print ne işe yarar" sorusunda iki tarih
cümlesi ve bir doğru print açıklaması gösteriliyordu. Ham kayıt değiştirilmeden
docs/evidence/notlarim-sohbet-first.json içine alındı.

## Değişiklik

1. Hybrid aramada sıralama ve eşik altından aday ekleme ayrıldı. Eşik üzerindeki
   belge için tek tam sözcük eşleşmesi artık BM25 sıralama katkısı yapar. Uzun
   sorularda eşik altındaki belgeyi kurtarmak için iki eşleşme şartı korunur.
   Cosine puanları ve mevcut embedding/SQLite verileri değiştirilmez.
2. Extractive modunda "X nedir", "X ne işe yarar", "X ne yapar" biçimindeki tek
   tanımlayıcı sorularında modele yalnız X sözcüğünü tam olarak içeren cümleler
   sunulur. X() biçimi de desteklenir; print ile printable eşleşmez. Kodda print
   veya diğer Python fonksiyonlarına özel cevap/anahtar sözcük listesi yoktur.
3. Model yine başka geçerli kimlikler seçerse bunlar cevaptan çıkarılır; çıkarılan
   kimlikler evidence_scope.excluded_ids içinde kaydedilir. Hiçbir uygun seçim
   kalmazsa invalid_evidence; kaynaklarda X yoksa model çağrılmadan no_context.
   Ham çıktı model_output içinde korunur.
4. Karşılaştırmalar ve uzun sorular bu dar tanım filtresine girmez. Genel
   generative moduna cümle filtresi uygulanmaz. Arama düzeltmesi her iki modu etkiler.

Bu filtre tam sözcük eşleşmesine dayalı sınırlı bir kuraldır; anlamsal doğruluk
ve eksiksizlik onayı değildir. Zamirle devam eden cümleleri dışarıda bırakabilir,
aynı tanımlayıcıyı kullanan ilgisiz bir cümleyi tutabilir. Eş anlamlı ifadeler veya
başka soru kalıpları için genel çözüm olarak sunulmamalıdır.

## Doğrulama

75 altyapı/SDK/arayüz testi geçti. Yeni testlerde farklı bir tanımlayıcı (flush)
kullanılarak sıralama, eşik altı koruma, tam sözcük eşleşmesi, karşılaştırma
bağlamı, geçersiz seçim ve kaynak yokken model çağrılmaması kontrol edildi.

Kayıtlı üç arama adayı yeniden sıralandığında:
01-degiskenler.txt, 04-fonksiyonlar.txt, 02-kosullar.txt.
Modelin yeni istemine sunulan dört cümlenin hepsi print içeriyor; tarih cümleleri
sunulmuyor. Bu, yalnız kayıttaki üç adayın kontrolüdür; tam indeks sorgusu değildir.

Eski kaynak sırası korunup gerçek ham model çıktısı yeniden işlendiğinde tarih
cümleleri çıkarıldı ve şu cevap kaldı:

> print yalnızca ekrana yazar; yazdırdığı değeri çağırana sonuç olarak vermez. [S2]

Önceki 24 sorunun kayıtlı çıktıları da eski kaynak sıralarıyla tekrar işlendi:
17 cevap metni aynı, 7 kapsam dışı ret korundu. Yeni sıralama veya istemle gerçek
modelden üretim yapılmadı; bu sonuç gelecekteki 24 soruluk deneyin yerine geçmez.
Kanıt docs/evidence/definition-fix-validation.json, tekrarlanabilir kontrol:

    python scripts/check_definition_fix.py

Hız düzeltmesi veya None ayrıntısı sorununun genel çözümü iddia edilmiyor.
Windows'ta güncel kodla kısa arayüz denemesi sıradadır.

## Windows güncellemesi

1. Çalışan PowerShell'de Ctrl+C ile arayüzü durdurun.
2. Güncel ZIP'in dosyalarını mevcut proje klasörüne kopyalayın. .venv, storage
   ve kişisel belgelerinizi koruyun.
3. İnternet kapalı kalabilir. Yeniden paket kurma, model indirme veya indeksleme
   gerekmez.
4. Arayüzü yeniden başlatın:

       .\.venv\Scripts\python.exe ui.py

5. Yeni oturumda "print ne işe yarar" ve "print ile return aynı şey mi?" sorularını
   sorun. Kaynak cümleleri modunu kullanın. Sohbeti JSON indirip paylaşın.

Dosya izleme kapalı olduğu ve model servisi önbellekte kaldığı için yalnız
tarayıcıyı yenilemek yeterli değildir; PowerShell süreci yeniden başlatılmalıdır.

