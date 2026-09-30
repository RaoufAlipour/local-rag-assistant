# Yerel RAG Asistanı — son teslim

Türkçe TXT, MD ve PDF belgelerinden kaynaklı cevap üreten yerel Python uygulaması.
Foundry Local, SQLite ve Streamlit kullanır. Son teslim; çalışan akademik prototip,
86 başarılı altyapı testi, Windows deneyleri, rapor ve sunumu içerir.

Arayüz yenilendi: koyu minimal tema, ortalanmış mesaj kutusu, sade sohbet
görünümü ve açılır kaynak bölümü. Ayrıntılar: `docs/UI-UPDATE.md`.

## Mevcut kurulumun güncellenmesi

1. Arayüzü PowerShell'de Ctrl+C ile durdurun.
2. ZIP içeriğini mevcut proje klasörüne kopyalayın. `.venv`, `storage` ve kendi belgelerinizi koruyun.
3. Aynı klasörde çalıştırın:

```powershell
.\.venv\Scripts\python.exe ui.py
```

Tarayıcı adresi: http://127.0.0.1:8501
Mevcut modeller yeniden indirilmez; yeniden indeksleme gerekmez.
Arayüz yerel katalog kullanır. Aynı soru ve cevap modu değişmemiş indekste tekrarlandığında
oturum önbelleği kullanılır ve bu durum ekranda belirtilir. Bu iyileştirme yeni sorulardaki
model gecikmesini ortadan kaldırmaz.

## Yeni Windows kurulumu

Kullanıcıda doğrulanan ortam: Windows 11, Python 3.13.3, 32 GB RAM, RTX 4070 Laptop GPU.
İlk bağımlılık ve model indirmeleri için internet gerekir. Model ağırlıkları ZIP içinde değildir.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-ui.txt
.\.venv\Scripts\python.exe main.py doctor
.\.venv\Scripts\python.exe main.py prepare --chat-model qwen2.5-7b --device cuda
.\.venv\Scripts\python.exe main.py snapshot --chat-model qwen2.5-7b --device cuda
.\.venv\Scripts\python.exe main.py ingest --offline
.\.venv\Scripts\python.exe ui.py
```

CUDA adımları NVIDIA cihaz hedefidir. Farklı donanımda uygun cihaz seçilmelidir.
Yerel katalog kaydı çevrimdışı kullanım içindir; işletim sistemi düzeyinde ağ engeli değildir.

## Teslim dosyaları

- `teslim/proje-raporu.pdf` ve `.md`: sonuçlar, mimari ve sınırlar.
- `teslim/proje-sunumu.pptx`: 8 slaytlık düzenlenebilir sunum; konuşmacı notları dahil.
- `teslim/DEMO.md`: kısa demo akışı.
- `teslim/deneme-belgesi.pdf`: kurgusal Pusula atölye belgesi; örnek ek belge.
- `docs/evidence/`: ham deney ve inceleme kayıtları.
- `docs/test-results-release.txt`: son 86 testin kaydı.

## Kullanım

Varsayılan extractive modu özgün kaynak cümlelerini gösterir. Generative modu modelin
serbest cevabını verir; kaynak etiketi anlamsal doğruluk garantisi değildir.
Belgeler ekranından dosya ekleyebilirsiniz. Sohbette kaynakları açabilir ve JSON indirebilirsiniz.
CLI seçenekleri: `python main.py --help`.

## Hız incelemesi

Kısa çevrimdışı karşılaştırma: `python scripts/check_speed.py`. Açık arayüzü önce
kapatın. Ayrıntılar: `docs/SPEED-CHECK.md`. Son hız araçlarıyla birlikte 90 otomatik
test geçti; gerçek cihazda hız kazancı henüz ölçülmedi.

## Bilinen sınırlar

Yeni sorular ve ilk yükleme uzun sürebilir. Son önbellek değişikliği işlevsel testlerle doğrulandı;
Windows hız kazancı için yeni ölçüm yapılmadı. OCR ve takip sorularına sohbet belleği yoktur.
Kapsam filtreleri bazı doğru soruları reddedebilir. Bir dosyayı klasörden silmek indeks kaydını
kendiliğinden silmez. Ayrıntılı ve güncel sonuçlar teslim raporundadır; eski docs raporları
önceki sürümlerin tarihsel kayıtlarıdır.

## Testleri geliştirme sırasında çalıştırma

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Model cevap kalitesi test sayısından ayrı değerlendirilir; 86 test, yüzde 100 cevap doğruluğu değildir.
