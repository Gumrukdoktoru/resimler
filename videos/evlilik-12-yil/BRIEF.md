---
workflow: general-video
flow: automation
storyboard: no
message: "Ufuk & Gülin — 12. yıl dönümümüz kutlu olsun; sonsuzluğa"
destination: phone (WhatsApp / Instagram)
aspect: 1080x1920
language: tr
length: 80s
---

## Intent

Ufuk ve Gülin'in 12. evlilik yıl dönümü için, birlikte çekilmiş 16 fotoğraftan
duygusal ve şık bir görsel şov. Kullanıcının sözleriyle: isimler "Ufuk-Gülin
Sonsuzluğa"; "sonsuzluk vurgusu olsun, ama 12. yıldönümüz kutlu olsun diye yazsın".

## Assets

- `assets/photos/foto-01.jpg … foto-16.jpg` — kullanıcının yüklediği 16 dikey fotoğraf
  (repo kökündeki WhatsApp Image *.jpeg dosyaları), gündüz → gece → gün doğumu balonları
  → gün batımı sırasıyla dizildi.
- `assets/music/piyano.wav` — `scripts/piyano.py` ile üretilen telifsiz piyano + yaylı
  parçası (66 BPM; her fotoğraf geçişi bir ölçü başına denk gelir).
- `assets/fonts/` — Pinyon Script (isimler, şiirsel satırlar) ve Josefin Sans (başlıklar), OFL lisanslı.

## Customizations

- Açılış: altın ∞ kendini çizer → "Ufuk & Gülin" → "12. YIL DÖNÜMÜMÜZ KUTLU OLSUN".
- Kapanış: 16 fotoğraf yuvarlak çerçevelerde ∞ şeklinde sonsuz döngüde döner →
  "Ufuk & Gülin" / "Sonsuzluğa…" / "12. YIL DÖNÜMÜMÜZ KUTLU OLSUN".
- Fotoğraflar üzerinde dört kısa satır: "Her yolculuk seninle güzel",
  "Gülüşün, en sevdiğim manzara", "Aynı tutku, aynı kalp", "Seninle gökyüzü bile yakın".

## Notes

- Kaynak düzenleme: `scripts/index.template.html` + `scripts/build_index.py` →
  `python3 scripts/build_index.py` ile `index.html` yeniden üretilir.
- Müzik yeniden üretimi: `pip install mido`, `apt install fluidsynth fluid-soundfont-gm`,
  sonra `python3 scripts/piyano.py assets/music/piyano.wav`.
