"""Render the Velana BIM montage with Pillow and FFmpeg."""
import argparse
import math
import subprocess
import tempfile
import wave
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H, FPS, DURATION = 1280, 720, 24, 26
PAPER = '#ece2cd'
INK = '#201b17'
RED = '#bd2c23'


def smooth(x):
    x = min(1, max(0, x))
    return x * x * (3 - 2 * x)


def render(materials, bim, fonts, output):
    @lru_cache(None)
    def face(size, bold=True):
        weight = 'Bold' if bold else 'Regular'
        return ImageFont.truetype(str(fonts / f'NotoSansCJK-{weight}.ttc'), size, index=2)

    def text(draw, xy, label, size, color=INK, bold=True):
        draw.text(xy, label, fill=color, font=face(size, bold), anchor='lt')

    def print_image(path, document=False):
        with Image.open(path) as raw:
            tone = ImageOps.grayscale(raw)
        tone = ImageOps.autocontrast(tone, cutoff=0.3)
        return ImageOps.colorize(tone, INK, '#f5ecd8' if document else PAPER)

    section = print_image(materials / '02_Construction/Drawings/Velana_Cross_Section_05.png', True)
    before = print_image(bim / 'Clash.png')
    after = print_image(bim / 'Resolved.png')
    noise = Image.effect_noise((W, H), 6).convert('RGB')

    def photo(canvas, pic, box, cover=True, zoom=1):
        x, y, w, h = box
        if zoom > 1:
            pic = ImageOps.fit(pic, (round(pic.width / zoom), round(pic.height / zoom)), centering=(.50, .50))
            cw, ch = round(pic.width / zoom), round(pic.height / zoom)
            dx, dy = (pic.width - cw) // 2, (pic.height - ch) // 2
            pic = pic.crop((dx, dy, dx + cw, dy + ch))
        fitted = (ImageOps.fit if cover else ImageOps.contain)(pic, (w, h), Image.Resampling.LANCZOS)
        canvas.paste(fitted, (x + (w - fitted.width) // 2, y + (h - fitted.height) // 2))
        return x + (w - fitted.width) // 2, y + (h - fitted.height) // 2, *fitted.size

    def label(draw, x, y, value, size=20, background=INK, foreground=PAPER):
        width = math.ceil(draw.textlength(value, font=face(size))) + 24
        draw.rectangle((x, y, x + width, y + size + 18), fill=background)
        text(draw, (x + 12, y + 7), value, size, foreground)

    def subtitle(draw, value):
        draw.rectangle((53, 641, 53 + math.ceil(draw.textlength(value, font=face(27))) + 31, 696), fill=INK)
        draw.rectangle((53, 641, 60, 696), fill=RED)
        text(draw, (73, 654), value, 27, PAPER)

    def stripe(draw, y, offset=0, fill=RED):
        draw.polygon([(-60 + offset, y), (1340 + offset, y - 440),
                      (1340 + offset, y - 352), (-60 + offset, y + 88)], fill=fill)

    def marker(draw, xy, radius=42):
        x, y = xy
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), outline=RED, width=6)
        draw.line((x+radius, y, x+radius+45, y-44, x+radius+93, y-44), fill=RED, width=4)
        label(draw, x+radius+93, y-61, 'CL-01', 17, RED)

    def frame(t):
        dark = 6 <= t < 14
        canvas = Image.new('RGB', (W, H), INK if dark else PAPER)
        d = ImageDraw.Draw(canvas)
        if t < 2:
            stripe(d, 590, int(-100 + 100 * smooth(t * 3)))
            text(d, (62, 45), '维拉娜国际机场  /  新航站楼', 23)
            text(d, (58, 177), '吊顶之上', 126)
            label(d, 65, 335, '从建筑总剖面到管综节点', 30)
        elif t < 6:
            stripe(d, 615)
            canvas.paste('#f5ecd8', (43, 150, 1237, 565))
            x, y, w, h = photo(canvas, section, (49, 154, 1182, 402), False)
            text(d, (54, 44), '建筑总剖面', 71)
            label(d, 51, 559, '项目图纸  /  CROSS SECTION 05')
            p = smooth((t - 2.5) / .5)
            if p > 0:
                d.rectangle((x+int(w*.50), y+int(h*.31), x+int(w*(.50+.22*p)), y+int(h*.73)), outline=RED, width=4)
            subtitle(d, '总剖面标出值机大厅上方的吊顶区域。')
        elif t < 10:
            stripe(d, 592)
            photo(canvas, before, (306, 55, 921, 553))
            label(d, 930, 60, 'BIM 模型示意')
            text(d, (57, 44), '吊顶管综', 60, PAPER)
            label(d, 57, 217, '暖通风管', 27)
            label(d, 57, 280, '弱电桥架', 27)
            if t >= 8:
                marker(d, (764, 330), 42)
            subtitle(d, '同一个吊顶空间里，暖通风管与弱电桥架交叉。')
        elif t < 14:
            photo(canvas, before, (352, 43, 876, 561))
            stripe(d, 683, fill=INK)
            text(d, (60, 123), '硬碰撞', 87, PAPER)
            label(d, 62, 232, 'CL-01', 31, RED)
            marker(d, (788, 319), 52)
            label(d, 946, 49, 'BIM 模型示意')
            subtitle(d, '碰撞检查标出两者实际相交的位置。')
        elif t < 22:
            stripe(d, 604)
            text(d, (52, 44), '调整桥架标高', 69)
            box_a, box_b = (53, 172, 574, 386), (650, 172, 574, 386)
            photo(canvas, before, box_a)
            if t >= 14.5:
                photo(canvas, after, box_b)
                label(d, 650, 173, '调整后', 23)
            label(d, 53, 173, '检查状态', 23, RED)
            marker(d, (342, 364), 30)
            label(d, 54, 575, '同一机位  /  BIM 模型示意')
            subtitle(d, '调整标高后，桥架从风管下方通过。')
        else:
            photo(canvas, after, (355, 51, 877, 571))
            stripe(d, 639)
            text(d, (58, 111), '复核', 118)
            label(d, 59, 269, '调整后节点', 27)
            label(d, 933, 56, 'BIM 模型示意')
            subtitle(d, '协调团队复核净空和支吊架。')

        blend = min(.20, .16 if dark else .17)
        canvas = Image.blend(canvas, noise, blend)
        d = ImageDraw.Draw(canvas)
        transition = next((t-cut for cut in (2, 6, 10, 14, 22) if 0 <= t-cut < .25), None)
        if transition is not None:
            x = int(1430 * (transition / .25) - 180)
            d.polygon([(x-185, 0), (x, 0), (x+224, H), (x+39, H)], fill=RED)
        return canvas

    def write_score(path):
        rate = 24000
        samples = bytearray()
        for i in range(DURATION * rate):
            t = i / rate
            beat = int(t * 2)
            age = t - beat / 2
            impact = beat in (0, 4, 12, 20, 28, 44)
            level = .22 if impact else (.10 if beat % 4 == 0 else .048)
            envelope = min(1, age * 220) * math.exp(-age * (15 if impact else 26))
            signal = level * envelope * (math.sin(2*math.pi*66*age) + .22*math.sin(2*math.pi*670*age))
            if t > 25.5:
                signal *= (26 - t) * 2
            samples.extend(int(signal * 32767).to_bytes(2, 'little', signed=True))
        with wave.open(str(path), 'wb') as f:
            f.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
            f.writeframes(samples)

    output.parent.mkdir(exist_ok=True, parents=True)
    with tempfile.TemporaryDirectory() as temp:
        score = Path(temp) / 'score.wav'
        write_score(score)
        with subprocess.Popen([
            'ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
            '-s', f'{W}x{H}', '-r', str(FPS), '-i', 'pipe:0', '-i', str(score),
            '-c:v', 'libx264', '-crf', '20', '-preset', 'fast', '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', str(output),
        ], stdin=subprocess.PIPE) as proc:
            try:
                for n in range(DURATION * FPS):
                    proc.stdin.write(frame(n / FPS).tobytes())
            finally:
                proc.stdin.close()
            if proc.wait():
                raise RuntimeError('FFmpeg could not render the trial cut.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--materials', type=Path, required=True)
    parser.add_argument('--bim', type=Path, required=True)
    parser.add_argument('--fonts', type=Path, default=Path('/usr/share/fonts/opentype/noto'))
    parser.add_argument('--output', type=Path, default=Path('output/Velana_BIM_Kino_Montage.mp4'))
    args = parser.parse_args()
    render(args.materials, args.bim, args.fonts, args.output)
