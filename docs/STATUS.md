# Son teslim durumu

Çalışan akademik prototip teslim edildi. 86 test başarılı. Son gerçek Windows kontrolünde sınav tarihi için uygun ret ve gün/saat sorusu için doğru cevap doğrulandı. Oturum içi tekrar-soru önbelleği eklendi; yeni sorulardaki gecikme tamamen çözülmüş değildir. Güncel sonuç ve sınırlar: `../teslim/proje-raporu.pdf`. Aşağıdaki notlar önceki sürümlerin tarihsel kaydıdır.

---

# İlerleme — 12 Eylül 2026

## Güncel durum

29 Eylül: yeni PDF Windows arayüzünden yüklenip sorgulandı. Altı soruda beş doğru
cevap, bir uygunsuz tarih alıntısı vardı. Kaynak cümleleri moduna olay-tarih
filtresi eklendi. 83 test ve kayıtlı çıktılarla regresyon kontrolü geçti.
Yeni kodun gerçek Windows denemesi henüz yok; genel ret ve hız sorunları açık.
İnceleme ve sonraki adım: `docs/EVENT-DATE-FIX.md`.

14 Eylül: kullanıcı arayüzden bir soru sordu ve sohbeti JSON olarak dışa aktardı.
Bu akış çalıştı; görsel görünüm ve altı belgenin arayüz listesi henüz doğrudan
incelenmedi. "print ne işe yarar" cevabına ilgisiz tarih alıntıları karıştı.
Sıralama ve tek tanımlayıcı tanım filtresi eklendi; 75 test geçti. Kaydın tekrar
işlenmesinde bu alıntılar çıktı. Yeni model üretimi kontrolü bekliyor.
Sıradaki adım `docs/DEFINITION-FIX.md`; tekrar bağımlılık kurmak gerekmiyor.

**Son güncelleme:** 24 soruluk extractive Windows deneyi incelendi. Doğru kaynak
17/17; 16 yeterli, 1 eksik ayrıntılı cevap. Ham durumlarda ret 5/7; boş JSON
listesi düzeltmesi ve aynı çıktıların yeniden işlenmesiyle 7/7. Bu yeni GPU
deneyi değildir. Arayüz (sohbet/kaynaklar/belge ekleme) hazır, 69 test geçti.
Windows GPU ile arayüz akışı henüz doğrulanmadı. Sıradaki adım
`docs/START-HERE-WINDOWS.md`; sonuçlar `docs/WINDOWS-QUALITY-V3-REVIEW.md`.
Tam kalite kabulü, gecikmenin nedeni, son rapor ve sunum açık kalıyor.

## Önceki aşamaların kaydı

Yeni kalite aşaması: `--answer-mode extractive` kaynak cümlelerini aynen
gösterir. 24 soruluk regresyon/genişletme listesi ve 60 başarılı altyapı testi
hazır. Gerçek modelin cümle seçimi Windows'ta henüz değerlendirilmedi;
eski üç cevap sorunu çözülmüş sayılmıyor. Kurulum veya indeks yenileme gerekmez.
Komut ve kabul ölçütleri: `docs/SOURCE-FAITHFUL-ANSWERS.md`.

**Windows CUDA ile internet kapalı 14 soruluk değerlendirme tamamlandı.**
snapshot/--offline yolu, kullanıcının bağlantıları kapatarak yaptığı yeni süreç
denemesinde çalıştı. Doğru belge 9/9, kapsam dışı ret 5/5. Üretilen 11 cevap ve
3 no_context sonucu çevrimiçi v2 ile aynı. Kaynak incelemesinde 6 cevap uygun,
3 cevap düzeltme gerektiriyor; print'in None döndürdüğü yanlış aktarılmış.
Proje son kalite kabulü tamamlanmadı. Son beş soruluk profilde ilk soru 27,78 saniye,
sonraki dört soru ortalama 2,96 saniye sürdü. İlk model yükleme 4,36 saniye,
ilk SDK yanıt çağrısı 23,16 saniye. Önceki aralıklı 21–24 saniyelik beklemeler
tekrarlanmadı; kök nedeni belirlenmedi. Katalog/oturum süreleri bu profilde küçük.

Güncel performans incelemesi `docs/WINDOWS-PROFILE-REVIEW.md` içindedir.

Güncel rapor `docs/WINDOWS-OFFLINE-REVIEW.md`. Bağlantı kesintisi kullanıcı beyanına
dayanır; bağımsız ağ trafiği kaydı değildir. Ham çıktı değiştirilmeden korunmuştur.

Hedef cihaz: Windows 11 (10.0.26200), Python 3.13.3, 32 GB RAM,
RTX 4070 Laptop GPU / 8188 MiB VRAM, NVIDIA 592.82. SDK 2.0.1, pypdf 6.18.0.
Kullanıcı model hazırlığı, indeksleme, çıkarım ve değerlendirme boyunca olası
Microsoft tanılama/cihaz verisi paylaşımını onayladı; tekrar onay bekleyen işlem yok.

Güncel ayrıntılar `docs/WINDOWS-CUDA-REVIEW-V2.md` içindedir. V2 ham kayıt ve ayrı
inceleme `docs/evidence/` altında saklanır. V2 incelemesi sırasında kod değiştirilmemişti;
sonraki katalog düzeltmesi Runtime/CLI'ye eklendi, RAG yönergesi değişmedi.

## İlk Windows deneyi (geçmiş kayıt)

| Kontrol | Kanıt / sonuç |
|---|---|
| CUDA kaydı ve modeller | Kullanıcı çıktısında iki CUDA varyantı hazırlanmış ve yüklenmiş |
| Hello | Qwen2.5 7B: Merhaba |
| İndeksleme | 6 belge, 6 parça; CUDA embedding modeli |
| Gerçek değerlendirme | Yüklenen windows-cuda-evaluation.json, 14/14 tamamlandı |
| Doğru kaynak getirme | Eski semantic aramada 8/9 |
| Cevap doğruluğu incelemesi | 5 tam uygun, 2 hassasiyet/terim sorunu, 2 bilgi hatası |
| Kapsam dışı davranış | Ham içerikte 5/5 ret; eski uygulama bunlardan birini yanlış sınıflandırmış |
| İlk soru süresi | 43,7171 sn; sohbet modelinin ilk yüklenmesini de içerir |
| Sonraki cevaplanabilir sorular | 1,70–5,66 sn; başlangıç/embedding yüklemesi hariç |
| Çevrimdışı Windows başlangıcı | Kullanıcı testi başarısız: Azure bölgelerine erişilemedi, embedding görev metadata'sı eksik |

İnceleme Codex'in kaynak karşılaştırmasıdır; öğretmen/kullanıcı onayı değildir.
Ham kayıt `docs/evidence/windows-cuda-evaluation.json` içinde değiştirilmeden saklanır.
Ayrıntılar `docs/WINDOWS-CUDA-REVIEW.md` ve `docs/evidence/windows-cuda-review.json` içindedir.

## Bu sürümde değişenler

- Ret cümlesinin sonundaki `[S1], [S2]` biçimi doğru ayrıştırılır. Ek iddialar ret sayılıp gizlenmez.
- Varsayılan arama cosine + BM25 sıralamalarını birleştirir; eski arama `--retrieval-mode semantic` ile seçilebilir.
- Kod terimleri korunur. Uzun sorgularda sözcük kolunun en az iki ayrı terimi eşleştirmesi gerekir;
  tek terimlik sorguda o terimin tam eşleşmesi yeterlidir. Bu bir doğruluk garantisi değildir.
- Yönerge, doğrudan kaynak desteğini ve teknik terimlere sadakati daha açık ister.
- Değerlendirme kaydı arama modunu ve yeni modülün kod özetini içerir.
- Belgeler ve embedding kimliği değişmedi; mevcut Windows indeksi kullanılabilir.

Yerel doğrulama: **42 test geçti, SDK bulunmadığından 2 SDK testi atlandı** (44 toplam).
Kayıt: `docs/test-results-quality-fix.txt`. Bu testler gerçek GPU kalite ölçümü değildir.
Yeni arama/yönerge Windows'ta tekrar değerlendirildi: 9/9 kaynak, 5/5 uygun ret.
Bu altyapı sonucu cevapların tümünün doğru olduğu anlamına gelmez; v2 incelemesine bakın.

## Sıradaki adım

Beş soruluk ölçüm tamamlandı; yeni zorunlu performans testi beklenmiyor.
Sıradaki geliştirme konusu kalan kaynak sadakati sorunları ve bağımsız kalite sorularıdır.
Arayüz/sunum teslimleri sonraki aşamadadır.

## Geçmiş deneyler

Linux 0.5B ve 1.5B deneyleri yeterli kalite sağlamadı. Linux 7B denemesi ilk cevap
alınmadan ortam bellek baskısı nedeniyle durdu; bu Windows sonucu değildir.
Linux ağ engeli doğrulandı fakat ağsız SDK açılışı katalog metadata hatası verdi.
Ham geçmiş kanıtlar `docs/evidence/`, açıklamalar `docs/QUALITY-NOTES.md` içindedir.
Paket model ağırlıkları, sanal ortam ve aktif cihaz veritabanını içermez.

## Yerel katalog çözüm adayı

`snapshot`, SDK'nın gerçek ModelInfo kayıtlarını cihazda saklar; model indirme/yükleme yapmaz.
`--offline`, SDK'nın desteklediği catalog_urls seçeneğini yalnız 127.0.0.1 üzerinde
çalışan salt okunur metadata servisine yönlendirir. Model kimliği, görev ve sağlayıcı
kontrolleri korunur. Varsayılan açılış yolu --offline verilmedikçe değişmez.
Yerel katalog SDK 2.0.1'in gerçek ayrıştırıcısıyla sınandı; ardından Windows CUDA
çıkarımı 14 soruda tamamlandı. Ayrıntılar `docs/OFFLINE-CATALOG.md` ve güncel
`docs/WINDOWS-OFFLINE-REVIEW.md` içindedir.
Yeni test sonucu 50/50 başarılıdır; SDK testleri de çalıştırıldı.
Kayıt: `docs/test-results-offline-catalog.txt`.

## Süre ölçümü güncellemesi

Generation model bulma/yükleme, session açma, request hazırlama, response üretme/okuma
ve kaynak kapatma aşamalarına ayrıldı. `generation_details` JSON'a eklenir.
`--limit 5` yalnız kısa tanılama içindir; tam kalite değerlendirmesi sayılmaz.
RAG yönergesi ve arama değişmedi. 52/52 test geçti: `docs/test-results-profiling.txt`.
Bu son profil incelemesinde yalnız raporlar güncellendi; uygulama kodu değiştirilmedi.
