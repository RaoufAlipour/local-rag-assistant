# Olay tarihi kontrolü - 29 Eylül 2026

## Gözlenen hata

Yeni PDF ile yapılan altı gerçek Windows arayüz sorusunun ilk beşi doğru
cevaplandı ve ilgili sayfalar kaynak gösterildi. Son soruda model, belgede
olmayan sınav tarihi yerine sürüm tarihini içeren giriş paragrafını seçti.
Ham çıktı docs/evidence/pusula-first.json içinde değiştirilmeden korunur.

## Uygulanan kontrol

Kaynak cümleleri (extractive) modunda, tek bir olay için "X tarihi",
"X hangi tarihte" gibi tanınan kalıplarda:
- Tarih sözcüğünden önceki olay adı alınır; sınırlı Türkçe ad eki eşleştirmesi yapılır.
- Modelin önüne yalnız bu olayla bağlantılı açık takvim ifadesi içeren cümleler konur.
- Olaydan sonra en fazla 120 karakter uzaklıktaki tarih veya olaydan önce
  en fazla 80 karakter uzaklıkta "tarihinde/günü" bağıyla gelen tarih kabul edilir.
- Araya giren belge/sürüm/hazırlanma/güncellenme gibi metadata işaretleri elenir.
- Uygun cümle yoksa LLM çağrılmadan no_context ve standart bilgi bulunamadı cevabı verilir.
- Model yine kapsam dışındaki bir kaynak kimliğini seçerse önceki seçim
  filtresi bunu çıkarır. Geçerli seçim kalmazsa invalid_evidence olur.

Soruların cevapları, Pusula adı veya sınav sözcüğüne özel bir cevap kodlanmadı.
Toplantı ve teslim gibi farklı olaylarla olumlu/olumsuz testler eklendi.
Arama algoritması, belge indeksi, embedding modeli ve model istemi değiştirilmedi.

Bu bir sınırlı kuraldır; genel anlamsal doğrulama değildir. Birden fazla olay
soran sorular, tanınmayan soru biçimleri, zamirle bağlı ayrı cümleler ve bazı
Türkçe ekler kapsam dışındadır. Tanınan soruda eş anlamlı bir olay adı veya
desteklenmeyen tarih biçimi kullanılmışsa doğru bilgi de elenebilir. Aynı cümlede
birbirinden farklı olay ve tarihler bulunduğunda hatalı eşleşme hâlâ mümkündür.
Generative moduna bu filtre uygulanmaz. Bütün kapsam dışı sorular çözülmüş sayılmaz.

## Doğrulama

83 test geçti (docs/test-results-event-date.txt). Yeni sekiz test; gerçek olay
tarihini koruma, başka belge tarihini eleme, PDF başlığının metne birleşmesi,
ad eki ve ISO tarih, ters cümle sırası, kapsam dışı kimlik ve etkilenmemesi
gereken soru kalıplarını kontrol eder. Model yerine test nesneleri kullanılır.

Kayıtlı sonuçların aynı kaynaklarla tekrar işlenmesinde:
- PDF'nin beş doğru cevabı aynı kaldı.
- Sınav tarihi sorusu no_context oldu; model çağrısı gerekmedi.
- Önceki 17 cevap metni aynı ve yedi uygun ret korundu.
- Son iki print sorusunun cevapları aynı kaldı.

Bu bir yeni GPU çalıştırması, yeni retrieval veya hız ölçümü değildir.
Windows'ta yeni kodla doğrulama bekliyor. Kanıt:
docs/evidence/event-date-validation.json.
Tekrarlanabilir kontrol:

    python scripts/check_event_date_fix.py

## Windows'ta uygulama

1. PowerShell'de Ctrl+C ile arayüzü durdurun.
2. Yeni ZIP'teki dosyaları mevcut proje klasörüne kopyalayın. .venv, storage ve
   kişisel belgelerinizi koruyun. Bağımlılık kurma veya yeniden indeksleme gerekmez.
3. İnternet kapalıyken arayüzü yeniden başlatın:

       .\.venv\Scripts\python.exe ui.py

4. Kaynak cümleleri modunda şu iki soruyu sorun:
   - Pusula atölyesinin sınav tarihi nedir?
   - Pusula atölyesi hangi günlerde, saat kaçta başlar?
5. Sohbeti JSON olarak indirip paylaşın.

İlk soruda bilgi bulunamadı; ikinci soruda salı/perşembe, 18.30 beklenir.
Altı soruluk PDF deneyinin tamamını yeniden çalıştırmak gerekmez.
Önceki yanıt sürelerindeki genel gecikme ve print-return karşılaştırmasındaki
eksik None ayrıntısı bu değişiklikle çözülmüş sayılmaz.

