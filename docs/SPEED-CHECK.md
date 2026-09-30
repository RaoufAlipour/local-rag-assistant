# Son ölçümün sonucu

64 token sınırıyla anlamlı hız kazancı gözlenmedi. İlk tam istek ortalamayı etkiledi.
Güncel analiz ve sonraki bellek karşılaştırması: `SPEED-RESULTS.md`.

# Hız ölçümü: çıktı sınırı karşılaştırması

Mevcut Windows kayıtlarında arama genellikle küçük pay tutuyor; model yüklemesi ve
SDK cevap çağrısı beklemeye hakim. Oturum oluşturma süresi çok küçük. SDK çağrısı
tek başına saf GPU hesaplama süresi veya token üretim hızı olarak yorumlanamaz.

Kaynak cümlesi seçiminde kısa JSON bekleniyor. 192 token sınırının 64'e indirilmesi
aday iyileştirmedir; model erken bitiriyorsa fark yaratmayabilir. Kesilmiş JSON veya
farklı cümle seçimi başarısız/karşılaştırılamaz sonuç olarak işaretlenir. Varsayılan
uygulama sınırı 192 olarak korundu; hız kazancı henüz cihazda doğrulanmadı.

## Tek komut

Önce açık arayüzü Ctrl+C ile kapatın; iki model süreci GPU belleğini paylaşmasın.
Ölçümü aynı güç koşullarında, tercihen adaptör bağlıyken yapın. Proje klasöründe:

```powershell
.\.venv\Scripts\python.exe scripts/check_speed.py
```

İndirme ve indeksleme yapmaz; mevcut modelleri, yerel kataloğu ve indeksi kullanır.
Kısa model hazırlama çağrısını ayrı tutar. Ardından aynı kaynaklar ve aynı soru
192, 64, 64, 192 sırasıyla dört kez işlenir. Uygulamanın cevap önbelleği kullanılmaz.
Her istekte bağımsız sohbet oturumu açılır; önceki cevaplar bağlama eklenmez.

Çıktı: `storage/speed-check.json`. Dosyada ham cevaplar, seçilen kimlikler, istek
metinleri, model yükleme ve SDK süreleri, ham cevabın uzunluğu ve sondaki boşluk sayısı
bulunur. `nvidia-smi` varsa GPU bellek/kullanım/P-state örnekleri saniyelik alınır;
GPU modeli sorunun kesin nedeni olarak yalnız bu örneklerden ilan edilmez.

İki sınırda da aynı geçerli cümle seçimleri oluşursa aday süre oranı hesaplanır.
Bu, anlamsal doğruluk onayı değildir. Tek soru, iki tekrar ve bir cihaz ölçümü
istatistiksel garanti sağlamaz; ilk tam istekte ek hazırlık olabilir. Ayrı tekil
süreler de incelenmelidir. Genel kalite testi yerine kısa tanı amaçlıdır.

Başka bir belge sorusu kullanılabilir:

```powershell
.\.venv\Scripts\python.exe scripts/check_speed.py --question "Dosyayı w modunda açınca önceki içerik ne olur?" --output storage/speed-check-files.json
```

## Kaynak ve yerel doğrulama

SDK'nin SearchOptions.max_output_tokens alanı kullanılır:
https://github.com/microsoft/Foundry-Local/blob/main/sdk_v2/python/README.md
Kurulu 2.0.1 session_types.py üzerinden seçenek doğrulandı. Yeni kontroller eksik
koşumda ve farklı/geçersiz seçimde hız kazancı ilan edilmediğini, çıktı sınırının
SDK'ye iletildiğini ve ham boşlukların ölçüldüğünü sınar. GPU performansı burada ölçülmedi.
