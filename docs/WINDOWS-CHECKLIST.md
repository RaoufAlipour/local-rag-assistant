# Windows doğrulama akışı

Hedef kullanıcı cihazı: Windows 11, 32 GB RAM, RTX 4070. İlk adım START-HERE-WINDOWS.md içindedir.
Bu kontrol kodun hazırlandığı Linux ortamından ayrıdır. Sonuç alınmadan Windows başarısı iddia edilmez.

11 Eylül güncellemesi: mevcut cihazda kurulum, CUDA hello, indeksleme ve ilk 14 soru
tamamlandı. Bu kullanıcı için sıradaki işlem START-HERE-WINDOWS.md içindeki yeni sürüm
değerlendirmesidir. Aşağıdaki liste temiz kurulumdan tam kabulü yeniden üretmek içindir.

1. ZIP'i yeni klasöre çıkarın; main.py bulunan klasörde PowerShell açın.
2. README'deki sanal ortam ve bağımlılık kurulumunu tamamlayın.
3. `scripts/system-info.ps1` dosyasını PowerShell'den çalıştırın. Windows, RAM, CPU, GPU
   ve proje Python paket sürümlerinin çıktısını paylaşın. Bu araç kurulum yapmaz.
4. `main.py models` ile cihaz kataloğunu doğrulayın. Seçilen sohbet modeli tüm komutlarda
   aynı `--chat-model` değeriyle kullanılmalıdır.
5. `prepare`, `hello`, `ingest`, `search`, `ask` sırasını README'deki Python yolu ile çalıştırın.
6. `evaluate --chat-model MODEL --output storage/windows-online.json` ile 14 soruyu ölçün.
   Yarım kalırsa aynı komuta `--resume` ekleyin. Sonuç dosyasını değiştirmeyin.
7. İnternet açıkken `snapshot --chat-model MODEL` çalıştırın. Program kapandıktan sonra
   internet bağlantısını elle kapatın. Yeni PowerShell açıp aynı modelle `ask ... --offline`
   deneyin. Ayrıntılı sıra START-HERE-WINDOWS.md içindedir.
8. Başarılıysa internet kapalıyken `evaluate --chat-model MODEL --offline --output storage/windows-offline.json`
   çalıştırın. Başarısızsa tam hata mesajını kaydedin; başarı olarak işaretlemeyin.
9. Cevapları `data/documents` ile karşılaştırın: doğru bilgi, doğru kaynak, kapsam dışında ret.

Notlar:
- `doctor` ve `report` model yüklemez. `report --output ...` ağsız rapor incelemeye uygundur.
- `storage/model-map.json` bu cihazın prepare adımında oluşturulur.
- Linux'tan üretilmiş SQLite vektörleri Windows GPU model varyantına uymayabilir.
  Paketin aktif veritabanı boş başlar; Windows'ta ingest ile yeni indeks oluşturun.
- Örnek Linux ölçümleri `docs/evidence/` altında varsa yalnız geçmiş deney kanıtıdır.
- Ağ açıkken yerel inference çalışması ile ağsız soğuk başlangıç ayrı kabul kontrolleridir.
