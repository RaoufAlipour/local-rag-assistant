# Windows: sıradaki adım arayüz

**29 Eylül - güncel sonraki adım:** `docs/EVENT-DATE-FIX.md` rehberini uygulayın.
Ctrl+C ile uygulamayı kapatıp yeni dosyaları kopyalayın ve `ui.py` ile yeniden
başlatın. Yeniden kurulum/indeksleme yok. Sınav tarihi ile gün/saat sorusunun
sonuçlarını sohbet JSON'u olarak paylaşın. Aşağıdaki adımlar geçmiş aşamalardır.

**14 Eylül — mevcut kullanıcı için sıradaki adım:** `docs/DEFINITION-FIX.md`
rehberini uygulayın. Arayüzü Ctrl+C ile kapatın, yeni dosyaları kopyalayın ve
aynı `ui.py` komutuyla başlatın. Paket/model indirme veya indeksleme gerekmez.
"print ne işe yarar" ve "print ile return aynı şey mi?" sorularının yeni
sohbet JSON'unu paylaşın. Aşağıdaki kurulum adımları ilk kurulum içindir.

24 soruluk kalite denemesi tamamlandı; yeniden çalıştırmak gerekmiyor.
17/17 doğru kaynak bulundu, 16 cevap yeterli ve bir karşılaştırma eksik ayrıntılı.
İki ret biçimi hatası düzeltildi; kayıtlı çıktılarla 7/7 ret doğrulandı.
Bu düzeltme yeni bir GPU deneyi değildir. Ayrıntılar: docs/WINDOWS-QUALITY-V3-REVIEW.md.

## 1. Güncelle

ZIP içindeki güncel dosyaları mevcut proje klasörüne kopyalayın; aynı adlı kod
ve rehber dosyalarını değiştirin. .venv, storage ve kendi belgelerinizi koruyun.

## 2. İnternet açıkken arayüzü kur

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ui.txt
```

## 3. İnterneti kapatıp aç

```powershell
.\.venv\Scripts\python.exe ui.py
```

Tarayıcı kendiliğinden açılmazsa http://127.0.0.1:8501 adresine gidin.
PowerShell açık kalmalı. Durdurmak için Ctrl+C kullanın.
Modelleri tekrar indirmek, snapshot almak veya altı notu yeniden indekslemek gerekmez.

## 4. İlk kullanım

Sohbet ekranında 6 belge göründüğünü kontrol edin. “break ile continue farkı nedir?”
sorusunu sorun; kaynak bölümünü açın. Belgeler sekmesini kontrol edin.
Ekran görüntüsünü ve varsa hatayı paylaşın. Windows'ta GPU + arayüz akışı burada
henüz denenmedi. 69 test, test modeliyle arayüz akışları ve yerel HTTP açılışı geçti.

Arayüzde sohbet, kaynak parçalarının tamamı, TXT/MD/PDF ekleme, klasörde değişen
belgeleri tarama ve sohbeti JSON indirme bulunur. Ayrıntılar: docs/LOCAL-UI.md.

## Açık işler

- Karşılaştırma cevabındaki None ayrıntısı; gereksiz ek alıntılar ve bağımsız kalite değerlendirmesi.
- SDK yanıt süresinin nedeni: son deney ortalaması 14,246 saniye; hız düzeltmesi yapılmadı.
- Windows arayüz denemesi, son rapor, sunum ve demo hazırlığı.

Terminal kullanılmaya devam edilebilir:

```powershell
.\.venv\Scripts\python.exe main.py chat --chat-model qwen2.5-7b --device cuda --offline --answer-mode extractive
```

Her soru bağımsızdır. İlk model açılışı süreye dahildir. Ham deneyler docs/evidence
altında korunur; son raporları docs/STATUS.md üzerinden takip edebilirsiniz.
