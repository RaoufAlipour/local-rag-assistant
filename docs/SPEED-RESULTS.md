# Windows hız ölçümü — 30 Eylül 2026

Kaynak: `evidence/windows-speed-check.json`. Soru: break ile continue farkı nedir?

| Çağrı | Çıktı sınırı | Süre (s) |
|---|---:|---:|
| İlk tam kaynak isteği | 192 | 25,1439 |
| İkinci | 64 | 13,5613 |
| Üçüncü | 64 | 13,5146 |
| Dördüncü | 192 | 13,5534 |

Dört çıktı aynı: S1.9 ve S1.10. Kaynakta break ve continue açıklamalarını seçiyorlar.
Hepsi 33 karakter; sondaki boşluk sayısı sıfır. Modelin 192 token üretmeye zorlandığı
veya gizli boşluklarla gecikmeye neden olduğu hipotezi bu örnekte desteklenmiyor.

192 limitinin son çağrısı ile 64 limitinin ortalaması yalnız yaklaşık %0,11 ayrışıyor.
Ham rapordaki 1,429 oranı ilk tam isteğin uzun sürmesinden etkileniyor; bu bir token
sınırı hız kazancı olarak sunulmamalı. İlk küçük TAMAM çağrısı uzun kaynak isteğinin
bütün hazırlığını ortadan kaldırmamış. Bunun SDK içindeki kesin nedeni ölçülmedi.
Araç artık iki 192 çağrısı %20'den fazla ayrıştığında hız oranını vermiyor.

GPU örneklerinde bellek 7872/8188 MiB (yaklaşık %96,1), kalan alan 316 MiB.
Ölçümün cevap üretme bölümlerinde kullanım çoğunlukla %100; GPU devrede.
Bu örnekler RAM'e taşma, bellek bant genişliği sınırı veya termal yavaşlama kanıtı değildir.
Arama 0,2332 s. Dört tam istekte tekrar model yüklenmemiş; oturum açma mikrosaniye
ölçeğinde. Ağırlıklı süre SDK cevap çağrısında.

## Sonraki kontrollü karşılaştırma

Aynı 41 kaynak cümlesi ve aynı 192 sınırı ile embedding modelinin kaldırılması sınanır.
İlk tam kaynak çağrısı hazırlama olarak dışlanır. İkinci çağrı iki model yüklüyken,
sonraki iki çağrı embedding modeli kaldırıldıktan sonra yapılır. Kaynaklar yeniden
aranmaz; istem aynı kalır. İndeks, model dosyaları ve uygulama ayarları değişmez.
Model çağrı sayısı dört; cevap önbelleği yoktur.

Önce çalışan arayüzü Ctrl+C ile kapatın, güncel paketi kopyalayın ve çalıştırın:

```powershell
.\.venv\Scripts\python.exe scripts/check_vram.py
```

Kayıt: `storage/vram-check.json`. GPU bellek örnekleri ve seçimlerin aynı kalıp
kalmadığı birlikte incelenmelidir. SDK unload işleminin bütün belleği serbest
bırakacağı varsayılmıyor; bellek örnekleri bu yüzden saklanıyor. Bu deney kazanım
sağlasa bile gerçek uygulamada sonraki soru için embedding yeniden yükleme maliyeti
ayrıca değerlendirilmelidir. Uygulamaya henüz yeni bellek stratejisi uygulanmadı.

## Embedding kaldırma deneyi

Gerçek Windows kaydı: `evidence/windows-vram-check.json`. İlk hazırlama 28,59 s,
iki model yüklüyken 9,76 s, embedding kaldırıldıktan sonra 24,93 ve 24,94 s.
Seçimler aynı. Bellek örnekleri her iki durumda 7872 MiB gösteriyor; beklenen boşalma
gözlenmedi. Sabit sıra ve az tekrar nedeniyle kesin neden belirlenmedi. Bu değişiklik
uygulamaya alınmadı. Sonraki adım: `MODEL-COMPARISON.md`.
