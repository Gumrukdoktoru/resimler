"""index.html üreteci — 12. yıl dönümü fotoğraf filmi (1080x1920, 80 sn).

Zamanlama müzikle aynı ızgarada: 66 BPM, bir ölçü = 240/66 sn.
  0 – 2 ölçü   : açılış — altın ∞ çizilir, "Ufuk & Gülin", "12. Yıl Dönümümüz Kutlu Olsun"
  2 – 18 ölçü  : 16 fotoğraf, her geçiş bir ölçü başına ortalanmış 1.2 sn çözülme
  18 – 22 ölçü : kapanış — fotoğraflar ∞ üzerinde sonsuza dek döner, "sonsuzluğa…"

Kullanım: python3 scripts/build_index.py  (proje kökünden)
"""

import json
from pathlib import Path

BAR = 240 / 66
XF = 1.2  # crossfade length, centred on each downbeat
TOTAL = 80.0
OUTRO = 18 * BAR  # 65.45s


def C(i):
    """Downbeat at which photo i is the dominant image."""
    return 2 * BAR + i * BAR


# file, focus-y for circle thumbnails (%), Ken Burns: y0, y1 (px offset of the 1080-wide image), s0, s1
PHOTOS = [
    ("foto-01.jpg", 26, -420, -140, 1.05, 1.00),
    ("foto-02.jpg", 62, -505, -360, 1.00, 1.07),
    ("foto-03.jpg", 60, -150, -400, 1.06, 1.00),
    ("foto-04.jpg", 56, -300, -450, 1.00, 1.06),
    ("foto-05.jpg", 62, -505, -380, 1.07, 1.00),
    ("foto-06.jpg", 48, -250, -380, 1.00, 1.06),
    ("foto-07.jpg", 45, -200, -350, 1.06, 1.00),
    ("foto-08.jpg", 34, -250, -110, 1.00, 1.05),
    ("foto-09.jpg", 50, -300, -200, 1.00, 1.07),
    ("foto-10.jpg", 38, -100, -250, 1.06, 1.00),
    ("foto-11.jpg", 36, 0, -150, 1.00, 1.05),
    ("foto-12.jpg", 46, -250, -400, 1.05, 1.00),
    ("foto-13.jpg", 52, -350, -200, 1.00, 1.06),
    ("foto-14.jpg", 55, -400, -300, 1.07, 1.00),
    ("foto-15.jpg", 62, 0, -505, 1.00, 1.00),
    ("foto-16.jpg", 46, -300, -450, 1.00, 1.06),
]

# poetic lines over the photos: (text, first photo index, last photo index, "top"|"bottom")
LINES = [
    ("Her yolculuk seninle güzel", 1, 2, "top"),
    ("Gülüşün, en sevdiğim manzara", 6, 7, "bottom"),
    ("Aynı tutku, aynı kalp", 9, 10, "bottom"),
    ("Seninle gökyüzü bile yakın", 13, 14, "top"),
]


def r(x):
    return round(x, 3)


def photo_clips():
    out = []
    for i, (f, _fy, *_kb) in enumerate(PHOTOS):
        start = C(i) - XF / 2
        end = (C(i + 1) if i < 15 else OUTRO) + XF / 2
        out.append(
            f'      <div id="p{i + 1:02d}" class="clip photo" data-start="{r(start)}" '
            f'data-duration="{r(end - start)}" data-track-index="1">\n'
            f'        <div class="photo-fade"><img class="photo-img" data-layout-allow-overflow src="assets/photos/{f}" alt="" /></div>\n'
            f"      </div>"
        )
    return "\n".join(out)


def line_clips():
    out = []
    for n, (text, a, b, pos) in enumerate(LINES, 1):
        start = C(a) + 0.2
        end = C(b + 1) - 0.4
        out.append(
            f'      <div id="line{n}" class="clip poem poem-{pos}" data-start="{r(start)}" '
            f'data-duration="{r(end - start)}" data-track-index="3">\n'
            f'        <div class="poem-shade"></div>\n'
            f'        <div class="poem-inner">\n'
            f'          <p class="poem-text">{text}</p>\n'
            f'          <div class="poem-rule"></div>\n'
            f"        </div>\n"
            f"      </div>"
        )
    return "\n".join(out)


def leaks():
    # one warm light leak per photo-to-photo seam (and intro → first photo)
    return "\n".join(f'        <div class="leak" data-layout-allow-overflow id="leak{i:02d}"></div>' for i in range(16))


def thumbs():
    return "\n".join(
        f'          <div class="thumb" id="t{i + 1:02d}"><div class="thumb-in" '
        f'style="background-image:url(assets/photos/{f});background-position:50% {fy}%"></div></div>'
        for i, (f, fy, *_r) in enumerate(PHOTOS)
    )


TEMPLATE = Path(__file__).with_name("index.template.html").read_text(encoding="utf-8")

html = (
    TEMPLATE.replace("{{PHOTOS}}", photo_clips())
    .replace("{{LINES}}", line_clips())
    .replace("{{LEAKS}}", leaks())
    .replace("{{THUMBS}}", thumbs())
    .replace("{{OUTRO_START}}", str(r(OUTRO - 0.55)))
    .replace("{{OUTRO_DUR}}", str(r(TOTAL - (OUTRO - 0.55))))
    .replace("{{INTRO_DUR}}", str(r(C(0) + 0.5)))
    .replace("{{TOTAL}}", str(TOTAL))
    .replace(
        "{{CONFIG}}",
        json.dumps(
            {
                "bar": BAR,
                "xf": XF,
                "total": TOTAL,
                "outro": OUTRO,
                "photos": [
                    {"id": f"p{i + 1:02d}", "start": C(i) - XF / 2, "end": (C(i + 1) if i < 15 else OUTRO) + XF / 2,
                     "y0": y0, "y1": y1, "s0": s0, "s1": s1}
                    for i, (_f, _fy, y0, y1, s0, s1) in enumerate(PHOTOS)
                ],
                "lines": [
                    {"id": f"line{n}", "start": C(a) + 0.2, "end": C(b + 1) - 0.4}
                    for n, (_t, a, b, _p) in enumerate(LINES, 1)
                ],
                "seams": [C(i) for i in range(16)],
            }
        ),
    )
)

out = Path(__file__).resolve().parent.parent / "index.html"
out.write_text(html, encoding="utf-8")
print(f"wrote {out}")
