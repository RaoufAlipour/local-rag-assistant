# Beş dakikalık demo

1. Mevcut kurulumda `.\.venv\Scripts\python.exe ui.py` çalıştırın. Tarayıcıda `http://127.0.0.1:8501` açın.
2. Extractive cevap modunu kullanın. Demo öncesi ilk soruyla modeli hazırlayın; ilk yükleme uzun sürebilir. Bu hazırlığı performans ölçümü gibi sunmayın.
3. “break ile continue farkı nedir?” sorun. Cevap ile kaynak cümlesini birlikte gösterin.
4. Aynı soruyu yeniden sorun. Önbellek açıklamasını gösterin: bu kez yeni model üretimi yapılmadı.
5. Pusula PDF’si zaten ekliyse “Atölye hangi günler ve saat kaçta?” sorun; kaynak sayfasını gösterin. Henüz ekli değilse teslim/deneme-belgesi.pdf dosyasını Belgeler ekranından ekleyebilirsiniz. Aynı belgeyi ikinci adla yeniden eklemeyin.
6. “Bu atölyenin sınav tarihi nedir?” sorun. Belgeden bulunamayan sınav tarihi için cevap üretilmemesini açıklayın.
7. Sohbeti JSON olarak indirin. Sunumdaki deney sonuçlarının tüm sorular için doğruluk garantisi olmadığını belirtin.

## Kapanış cümlesi
Belge işleme, yerel arama ve kaynaklı cevap üretimi tamamlandı. Son sürüm tekrar soruları önbellekten karşılıyor. Yeni sorulardaki değişken gecikme ve kapsam filtrelerinin sınırlılığı raporda açıkça belirtilmiştir.
