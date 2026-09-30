# Minimal sohbet arayüzü

Kullanıcının paylaştığı koyu ChatGPT ekranı referans alınarak arayüz sadeleştirildi:

- Siyah/koyu gri arka plan, açık renk yazılar.
- Solda yeni sohbet, sohbet/belgeler geçişi ve kapalı Ayarlar bölümü.
- Boş ekranda ortalanmış başlık ve hemen altında yuvarlak mesaj kutusu.
- Sohbet sırasında sağda kullanıcı balonları, sade asistan cevapları ve altta mesaj kutusu.
- Kaynaklar cevap altında tek bir açılır bölümdedir.
- Öneri kartları, rozetler, dekoratif marka kutuları ve büyük karşılama metni kaldırıldı.

Model, indeks, önbellek ve belge yükleme mantığı değişmedi. Mesaj ve kaynak metinleri
HTML olarak yorumlanmaz. Bu uygulama ses, zamanlanmış görevler veya kalıcı sohbet listesi
sunmaz; referanstaki bu işlevlere ait düğmeler eklenmedi.

## Güncelleme

Uygulamayı Ctrl+C ile kapatın. ZIP içeriğini mevcut proje klasörüne kopyalayın;
.venv, storage ve kendi belgelerinizi koruyun. Sonra:

```powershell
.\.venv\Scripts\python.exe ui.py
```

Yeniden model indirme veya indeksleme gerekmez.

## Kontrol

Dört mevcut Streamlit AppTest kontrolü geçti: sohbet, geçmiş temizleme, belge ekranı,
boş indeks ve hata davranışları kapsanır. Testler örnek servisle çalışır; model çalıştırmaz.
Bu ortamda tarayıcı bulunmadığından piksel düzeyinde görsel doğrulama yapılmadı.
