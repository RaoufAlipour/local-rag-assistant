# Yerel RAG Asistanı

## Proje raporu • Son teslim

Türkçe belgeler üzerinde çalışan, kaynaklı cevap üreten yerel bir akademik prototip. Python, SQLite, Microsoft Foundry Local ve Streamlit kullanıldı. İlk kurulum ve model indirmelerinden sonra yerel katalogla çevrimdışı kullanım desteklenir.

## Tamamlanan ürün

TXT, MD ve metin içeren PDF okuma; belge parçalama; yerel embedding; SQLite indeksi; hibrit arama; kaynak gösterimi; terminal ve tarayıcı arayüzü; belge yükleme ve sohbet kaydı dışa aktarma tamamlandı.

## Teslim kapsamı

Kaynak kodu, altı Türkçe Python notu, 86 başarılı otomatik testin kaydı, Windows deney kayıtları, bu rapor, düzenlenebilir sunum ve demo rehberi pakete dahildir. Model ağırlıkları, sanal ortam ve kullanıcının veritabanı pakete dahil değildir.

## Sonuç nasıl okunmalı?

Çalışan ve belgelenmiş bir prototip teslim edilmektedir. Kaynak etiketinin doğru olması tek başına cevabın doğru veya yeterli olduğunu kanıtlamaz. Yeni soruların gecikmesi ve sınırlı kapsam filtreleri bilinen sınırlardır.

# Sistem ve uygulama

## Belgeden cevaba

Belgeler sayfa bilgisi korunarak yaklaşık 180 kelimelik, 30 kelime örtüşmeli parçalara ayrılır. qwen3-embedding-0.6b ile üretilen 1024 boyutlu vektörler, kaynak metniyle SQLite içinde saklanır. Soru için cosine similarity ve BM25 tabanlı sıralamalar RRF ile birleştirilir; en fazla üç parça seçilir.

## Cevap biçimleri

Arayüzün varsayılan extractive modunda model kaynak cümlesi kimliklerini seçer; uygulama özgün cümleleri gösterir. Generative modu serbest, kaynak etiketli cevap üretir. Tanım ve olay-tarih kapsam filtreleri extractive modunda uygulanır; bunlar genel bir doğruluk garantisi değildir.

## Çalıştırılan ortam

Kullanıcı çıktıları: Windows 11, Python 3.13.3, 32 GB RAM, NVIDIA RTX 4070 Laptop GPU (8188 MiB), sürücü 592.82. Foundry Local SDK 2.0.1, pypdf 6.18.0. Sohbet: qwen2.5-7b-instruct-cuda-gpu:4; embedding: qwen3-embedding-0.6b-cuda-gpu:1.

## Çevrimdışı kullanım

prepare modelleri hazırlar; snapshot görev ve varyant bilgilerini storage/offline-models.json dosyasına kaydeder. --offline bu yerel kataloğu kullanır. Bu seçenek işletim sistemi düzeyinde ağ engeli değildir; çevrimdışı kullanıcı denemeleri bağımsız bir paket yakalama ölçümü olarak sunulmamıştır.

# Doğrulama ve kalite

## Otomatik testler: 86 başarılı

Son kodda veritabanı, arama, kaynak seçimi, kapsam filtreleri, dosya yükleme ve oturum önbelleği kontrolleri geçti. Bu sayı model cevaplarının doğruluk oranı değildir. Kayıt: docs/test-results-release.txt.

## 24 soruluk Windows deneyi

17 cevaplanabilir sorunun 17’sinde beklenen kaynak bulundu. Cevap incelemesinde 16 cevap yeterli, bir cevap eksik ayrıntılıydı. Yedi kapsam dışı soruda beş uygun ret ve iki invalid_evidence oluştu. Boş liste ayrıştırma düzeltmesiyle kayıt tekrarında yedi uygun ret elde edildi; bu tekrar yeni bir GPU deneyi değildir.

## Yeni PDF ile genelleme denemesi

Pusula atölye PDF’sinde beş bilgi sorusu doğru cevaplandı. Olmayan sınav tarihi sorusunda belge sürüm tarihi seçildi. Olay-tarih filtresi eklendikten sonraki gerçek Windows kontrolünde sınav sorusu no_context ile reddedildi; gün/saat sorusu doğru cevaplandı. Son kontrol iki sorudur, bütün deneyin yeniden koşumu değildir.

## Kanıt dosyaları

docs/evidence/windows-cuda-quality-v3.json; ilgili review ve replay kayıtları; docs/evidence/pusula-first.json; docs/evidence/pusula-date-fix-windows.json. Eski raporlar tarihsel durumu yansıtır; güncel teslim özeti bu rapordur.

# Performans ve sınırlar

## Ölçülen süreler değişken

Beş soruluk önceki profilde ilk soru 27,78 saniye, sonraki dört soru ortalama 2,96 saniyeydi. 24 soruluk deneyin ortalaması 14,246 saniyeydi. Son PDF kontrolünün ilk model gerektiren sorusu 49,55 saniye sürdü: yaklaşık 12,28 saniye model yükleme, 35,97 saniye SDK cevap çağrısı. Bu değerler ayrı koşumlardır.

## Son hız iyileştirmesi

Arayüzde aynı soru, aynı cevap modu ve değişmemiş indeks için 32 kayıtlık oturum önbelleği eklendi. Tekrarlanan soruda model çağrısı atlanır; sonuç önbellekten geldiği belirtilerek gösterilir. İndeks içeriği değişirse önceki cevap kullanılmaz. Testlerle davranış doğrulandı; Windows üzerinde yeni bir hız ölçümü yapılmadı.

## Açık performans sınırı

Önbellek yeni soruları hızlandırmaz. İlk model yüklemesi ve SDK çağrısındaki uzun beklemeler tamamen çözülmüş değildir. Demo öncesi ilk soruyla modeli hazırlamak beklemeyi sunum dışına taşır; bu, yeni sorular için süre garantisi sağlamaz.

## Diğer sınırlar

Taranmış PDF için OCR yoktur. Kapsam filtreleri Türkçe kalıp ve sözcük eşleşmesine dayanır; yanlış ret mümkündür. Sohbet geçmişi takip sorusuna bağlam olarak verilmez. Kaynak dosyasını klasörden silmek indeks kaydını otomatik silmez. Generative cevaplar ayrıca insan incelemesi gerektirir.

# Kullanım ve teslim

## Mevcut kurulumu güncelleme

Arayüzü Ctrl+C ile durdurun. ZIP içeriğini mevcut proje klasörüne kopyalayın; .venv ve storage klasörlerini koruyun. PowerShell’de .\.venv\Scripts\python.exe ui.py komutuyla başlatın. Yeniden model indirme veya indeks oluşturma gerekmez.

## Kısa demo

Python notlarından “break ile continue farkı nedir?” sorusunu sorun, kaynak metni açın. Aynı soruyu tekrar sorarak önbellek etiketini gösterin. Pusula PDF’si indeksteyse gün/saat sorusunu ve belgede bulunmayan sınav tarihi sorusunu gösterin. Son olarak sohbeti JSON olarak indirin.

## Teslimin içeriği

teslim/DEMO.md: adım adım demo. teslim/proje-sunumu.pptx: düzenlenebilir sunum. teslim/proje-raporu.md: düzenlenebilir rapor metni. docs/evidence: ham deneyler. README.md: mevcut kullanıcı ve yeni kurulum yönergeleri.

## Geliştirme sonrası olası çalışmalar

Daha geniş bağımsız soru kümesi, takip sorularında bağlam, OCR, indeks silme yönetimi ve gerçek cihaz üzerinde gecikmenin SDK düzeyinde incelenmesi gelecekteki geliştirmelerdir. Bunlar bu teslimin tamamlanmış özellikleri olarak sayılmamıştır.
