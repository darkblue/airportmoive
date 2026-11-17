"""Photography-led second cut. Requires the original media pack and selected design stills."""
import os
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import full_film as film

PAPER, INK, BLUE, AQUA, SAND = '#f2f1e9', '#101d24', '#19475b', '#258b89', '#c28755'

DESIGN = {9: 'image26', 11: 'image19', 17: 'image22', 20: 'image45', 38: 'image13'}
DATA = {
    15: ('先安排暖通吊装', ('同区作业重叠', '暖通先吊装', '弱电进场安装')),
    19: ('机型和机位重新匹配', ('机型变更', '检查尺寸与占用', '运行人员确认')),
    22: ('服务切换', ('A 机房中断', '健康检查', 'B 机房接管')),
    29: ('门禁与告警', ('身份核验', '授权通行', '告警处置')),
    30: ('验证运行准备', ('单机测试', '接口联调', '全流程演练')),
    32: ('01  /  读码失败', ('测试箱进线', '未能读码', '转人工')),
    34: ('03  /  复扫通过', ('重新扫描', '核对记录', '恢复运行')),
}

def factory(materials, bim, fonts):
    media = Path(os.environ.get('VELANA_DESIGN_STILLS', 'design-stills'))
    credits = film.source_labels(materials)

    @lru_cache(maxsize=55)
    def face(size, regular):
        name = 'Regular' if regular else 'Bold'
        return ImageFont.truetype(str(fonts / f'NotoSansCJK-{name}.ttc'), size, index=2)

    @lru_cache(maxsize=100)
    def photo(path, w, h, fill):
        with Image.open(path) as image:
            img = image.convert('RGB')
        fn = ImageOps.fit if fill else ImageOps.contain
        return fn(img,(w,h),Image.Resampling.LANCZOS)

    def frame(number, shot, part, mode):
        start, stop, chapter, ref, title, lines = shot
        files = ref.split('|')
        image = Image.new('RGB',(1280,720),PAPER)
        d = ImageDraw.Draw(image)

        def txt(x,y,s,z,color=INK,regular=False,anchor='lt'):
            d.text((x,y),s,font=face(z,regular),fill=color,anchor=anchor)

        def put(path, box, fill=False):
            x,y,w,h = box
            obj = photo(path,w,h,fill)
            image.paste(obj,(x+(w-obj.width)//2,y+(h-obj.height)//2))

        def design(key):
            return media / f'{key}.jpg'

        def label(title, section='航站楼扩建'):
            txt(54,35,section,17,AQUA)
            txt(52,68,title,46)

        def footer(source, dark=False, headline=None):
            d.rectangle((0,608,1280,720),fill=INK if dark else PAPER)
            d.line((52,608,1228,608),fill='#38545e' if dark else '#bfcac4')
            fg = '#f5f5eb' if dark else INK
            alt = '#b9c9cc' if dark else '#4d696f'
            if headline:
                txt(53,622,headline,18,fg)
            txt(1226,622,source,16,alt,True,'rt')
            txt(53,657,lines[part],27,fg)

        def documentary(path, source, name=title):
            nonlocal image
            d.rectangle((0,0,1280,608),fill=INK)
            # Centre-fit with a matching dark background for portrait/4:3 archive.
            with Image.open(path) as raw:
                wide = raw.width/raw.height > 1.72
            put(path,(0,0,1280,608),wide)
            footer(source,True,name)

        def path_picture(path):
            return materials / path

        if number in (2,20,36):
            base = media / 'gates.jpg'
            if not base.exists():
                base = path_picture(f'{film.IT}/T1_Lounge_Mihaaru.jpg')
            if number == 36:
                base = path_picture(files[0])
            elif number == 20:
                base = design(DESIGN[20])
            put(base,(0,0,780,608),True)
            d.rectangle((780,0,1280,608),fill=INK)
            txt(828,56,'DEPARTURES',26,'#66d7c8')
            txt(828,101,'登机口',27,'#d0dfe3')
            gate = 'B04' if mode == 0 and number != 36 else 'B06'
            txt(813,186,gate,146,'#f4f3e9')
            txt(830,373,'登机口变更' if number != 36 else '前往登机',26,'#66d7c8')
            txt(830,552,'模拟航班  /  演示航显',17,'#c0ced2',True)
            footer('建筑设计效果图' if number == 20 else '旅客流程情景示意',True,title)
        elif number in (5,7):
            label(title,'机场档案' if number==5 else '旅客数据')
            if number == 5:
                items = [('1960','首架飞机降落'),('1966','胡鲁累机场启用'),('1981','国际航站楼启用'),('2025','新国际航站楼启用')]
                d.line((67,344,1205,344),fill='#9bb9b6',width=3)
                for i,(yr,event) in enumerate(items):
                    x = 67 + i*298
                    txt(x,235,yr,65,BLUE)
                    d.ellipse((x,335,x+17,352),fill=AQUA)
                    txt(x,377,event,23)
                footer('来源：Maldives Airports Company Limited')
            else:
                d.line((60,522,1200,522),fill='#aebdbb',width=2)
                for i,(yr,n) in enumerate([(2019,405),(2024,496),(2025,537)]):
                    x = 140+i*360
                    y = 522-round(n*.54)
                    d.rectangle((x,y,x+238,521),fill=('#9bc6c0','#5aa8a2',AQUA)[i])
                    txt(x,y-58,str(n),52,BLUE)
                    txt(x,539,str(yr),23)
                txt(1200,187,'单位：万人次',20,AQUA,True,'rt')
                footer('来源：Maldives Bureau of Statistics')
        elif number == 11 and part == 1 and (media/'ceiling.jpg').exists():
            documentary(media/'ceiling.jpg','1PAX｜项目摄影','完工大厅 · 吊顶细节')
        elif number in (9,11,12,13,14,16,17,28,33):
            label(title,'施工图与模型')
            if number == 14:
                for x,name,caption in [(53,'Clash.png','调整前'),(650,'Resolved.png','调整后')]:
                    put(bim/name,(x,159,575,404))
                    txt(x,563,caption,21,BLUE)
                footer('BIM 模型示意｜同一机位')
            else:
                if number in (13,16):
                    path = bim/('Clash.png' if number==13 else 'Resolved.png')
                elif number in DESIGN:
                    path = design(DESIGN[number])
                else:
                    path = path_picture(files[min(mode,len(files)-1)])
                put(path,(53,143,1174,458))
                footer('建筑设计报告' if number in (9,11,12,17) else '工程模型示意')
        elif number in DATA:
            headline,steps = DATA[number]
            label(headline,'施工协调示意' if number==15 else ('运行准备演练' if number in (30,32,34) else '系统运行示意'))
            current = min(2,mode if ref.startswith('@') else (0 if number==32 else 2))
            d.line((100,385,1150,385),fill='#b8cfca',width=3)
            for i,s in enumerate(steps):
                x=100+377*i
                on=i<=current
                d.ellipse((x-9,376,x+9,394),fill=AQUA if on else '#b9cfca')
                txt(x,235,f'0{i+1}',68,AQUA if on else '#8fa6a4')
                txt(x,423,s,32,INK if on else '#55747b')
            footer('运行场景示意')
        elif number in (18,21,23,24,26,37):
            label(title,'航站楼系统')
            # Readable technical plates; preserve their aspect ratios and legends.
            put(path_picture(files[0]),(52,143,1176,454))
            footer('二维声场覆盖示意' if number==26 else '演示资料')
        elif number==3:
            path=path_picture(files[mode])
            aerial = media/'aerial.jpg'
            if mode == 2 and aerial.exists():
                documentary(aerial,'1PAX｜项目摄影','胡鲁累岛 · 维拉娜国际机场')
            else:
                d.rectangle((0,0,1280,608),fill='#0c2736')
                with Image.open(path) as raw:
                    if mode < 2:
                        crop = raw.crop((0,int(raw.height*.21),raw.width,int(raw.height*.88))).convert('RGB')
                        mapped = ImageOps.contain(crop,(1280,608),Image.Resampling.LANCZOS)
                        image.paste(mapped,((1280-mapped.width)//2,(608-mapped.height)//2))
                    else:
                        put(path,(0,0,1280,608))
                footer(('底图：Natural Earth','底图：Natural Earth','TMA / ICAO')[mode],True,title)
        elif number in (6,8):
            for i,path in enumerate(files):
                new = media/('facade.jpg' if number==6 else 'lobby.jpg')
                use_new = new.exists() and ((number==6 and i==1) or (number==8 and i==0))
                put(new if use_new else path_picture(path),(i*640,0,640,530),True)
                d.rectangle((i*640,530,i*640+640,608),fill=INK)
                txt(i*640+28,553,('旧航站楼','新航站楼')[i] if number==6 else ('出发值机','到达行李提取')[i],24,'#f2f1e9')
            footer('照片：1PAX / ' + ('StromBer' if number==6 else 'Fayaz Moosa'),True,title)
        elif number == 38:
            final = media/'terminal.jpg'
            documentary(final if final.exists() and part==1 else design(DESIGN[number]),
                        '1PAX｜项目摄影' if final.exists() and part==1 else '建筑设计报告｜规划效果图',
                        '维拉娜国际机场  /  VELANA INTERNATIONAL AIRPORT')
        else:
            selected=files[min(mode,len(files)-1)]
            alternate = media/({10:'site.jpg',25:'gates.jpg',27:'checkin.jpg'}.get(number,'unused'))
            if alternate.exists():
                documentary(alternate,'1PAX｜项目摄影')
            else:
                path = path_picture(selected)
                if path.suffix.lower() in ('.jpg','.jpeg'):
                    documentary(path,credits.get(selected,'现场资料'))
                elif number==1:
                    d.rectangle((0,0,1280,608),fill=INK)
                    put(path,(50,20,1180,565))
                    footer('道具登机牌 · 模拟航班',True,title)
                else:
                    label(title,'项目记录')
                    put(path,(56,145,1168,453))
                    footer('素材来源：项目资料或演示图')
        return image
    return frame

film.make_frame_factory = factory
if __name__ == '__main__':
    import argparse
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--materials', type=Path, required=True)
    cli.add_argument('--bim', type=Path, required=True)
    cli.add_argument('--fonts', type=Path, default=Path('/usr/share/fonts/opentype/noto'))
    cli.add_argument('--output', type=Path, required=True)
    film.render(cli.parse_args(), editorial=True)
