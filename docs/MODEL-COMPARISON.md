# Daha küçük model karşılaştırması

Aday: qwen3-4b. Mevcut: qwen2.5-7b. Embedding modeli ve indeks aynı kalır.
Aday daha önce kullanıcı CUDA kataloğunda listelenmiştir; hazırlık mevcut katalogdan
uygun CUDA varyantını yeniden doğrular. CPU'ya otomatik geçilmez.

## 1. Güncelleme ve hazırlık — internet açık

Arayüzü Ctrl+C ile kapatın. Güncel ZIP içeriğini kopyalayın; .venv, storage ve belgeleri koruyun.

```powershell
.\.venv\Scripts\python.exe scripts/compare_models.py prepare
```

Yalnız aday model hazırlanır. Var olan 7B ve embedding model dosyaları silinmez.
Yerel katalogdaki diğer kayıtlar korunarak aday eklenir. Uygulamanın varsayılan modeli
7B olarak kalır. Model indirme boyutu gerçek katalog çıktısında görülebilir.

## 2. Karşılaştırma — internet kapalı olabilir

```powershell
.\.venv\Scripts\python.exe scripts/compare_models.py run
```

Önce 7B, sonra 4B ayrı Python süreçlerinde çalışır. İlk süreç bitmeden ikincisi açılmaz;
unload işleminin ölçümde belleği azaltmaması nedeniyle süreç sınırı kullanılır.
İki model için de tam kaynak isteğiyle ilk hazırlama çağrısı ayrı kaydedilir; beş
soruluk sonuç listesine katılmaz. Her model üç bilgi ve iki kapsam dışı soruyu yanıtlar.
Toplam 12 model/RAG çağrısı vardır; kapsam dışı sorular model çağrısı gerektirmeyebilir.
Bu kısa bir karşılaştırmadır, tüm kalite kümesinin yerine geçmez. Cevap önbelleği yoktur.

Çıktı: storage/models-comparison.json. Model kimlikleri, indeks özetleri, ham cevaplar,
seçilen kaynaklar, süreler, beklenen açıklamalar ve GPU örnekleri kaydedilir.
Model yükleme süresi hazırlama kaydında bulunur. Aynı kaynak etiketini kullanmak
cevabın yeterli olduğunu kanıtlamaz; cevaplar beklenen açıklamalarla incelenmelidir.
Üç bilgi sorusunun süreleri ayrıca karşılaştırılmalı; hızlı retler bunlarla karıştırılmamalıdır.

Qwen3 için /no_think yönergesi istenir. Bu bir metin yönergesidir; Foundry varyantında
uyulacağı garanti edilmez. Yalnız boş <think> kabuğu ayrıştırma öncesi çıkarılır;
dolu düşünce metni gizlenmez ve ham SDK çıktısı korunur. Mevcut 7B yolu değişmez.
Kaynak: https://huggingface.co/Qwen/Qwen3-4B

Hız veya kalite ölçülmeden aday varsayılan yapılmaz. Yeni UI kurulumu ve yeniden
belge indeksleme gerekmez. Karşılaştırma bittiğinde mevcut ui.py komutu yine 7B'yi açar.
