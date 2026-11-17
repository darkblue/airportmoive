"""Render the 38-shot Velana T1 blueprint film."""
import argparse
from functools import lru_cache
import json
import math
from pathlib import Path
import subprocess
import tempfile
from xml.etree import ElementTree as ET

from PIL import Image, ImageDraw
import build_blueprint as bp
import full_film as base

FPS=24
SIZE=(1280,720)
PAPER='#204580'
WASH='#789eca'
CHAPTERS=[0,45,140,265,325,360]

def thru(points,weight=2,fill='none',closed=False):
    return bp.path('M'+'L'.join(f'{x} {y}' for x,y in points)+('Z' if closed else ''),weight,fill)

def plain(x,y,txt,size=25):
    return bp.text(x,y,txt,size)

def multiline(text, width, x, y, size=24, spacing=36):
    words=[]
    for token in text.splitlines():
        while token:
            cut=min(width,len(token))
            if cut<len(token) and token[cut].isascii() and token[cut-1].isascii():
                split=token.rfind(' ',max(2,cut-11),cut)
                if split>0:cut=split
            words.append(token[:cut].strip())
            token=token[cut:].strip()
    return ''.join(plain(x,y+i*spacing,word,size) for i,word in enumerate(words))

def plan(kind):
    if kind=='ticket':
        return [bp.rect(170,220,800,329,3),bp.line(741,221,741,548,1.2,'stroke-dasharray="8 7"'),
           plain(197,261,'VELANA INTERNATIONAL AIRPORT',19),plain(197,347,'登机牌',50),
           plain(785,320,'GATE',21),plain(777,409,'B04',65),
           ''.join(bp.line(202+v*8,433,202+v*8,486,1+v%3) for v in range(48))]
    if kind in ('gate','route','ending'):
        gate='B04  →  B06' if kind=='gate' else ('B06' if kind=='route' else 'MLE')
        return [thru([(145,519),(737,519),(956,321),(956,227)],3),
                thru([(145,588),(782,588),(1038,359),(1038,227)],3),
                bp.path('M178 555H751L998 335V251',2.4,'none','stroke-dasharray="12 6" marker-end="url(#arrow)"'),
                bp.rect(525,222,405,139,2.5),plain(550,260,'DEPARTURES  /  登机口',19),plain(548,323,gate,54)]
    if kind=='atoll':
        return [thru([(145,414),(202,344),(296,333),(320,371),(366,413),(331,459),(198,474)],2.3,'url(#hatchSparse)',True),
                thru([(689,423),(740,369),(849,365),(946,416),(900,473),(789,491),(728,460)],2.3,'url(#hatchSparse)',True),
                bp.path('M314 468Q519 585 734 482',2,'none','stroke-dasharray="12 7" marker-end="url(#arrow)"'),
                plain(192,307,'机场岛',27),plain(750,327,'度假岛',27),plain(474,569,'海上接驳',22)]
    if kind=='hall':
        return [bp.rect(133,231,949,370,3),bp.line(140,285,1076,285,1.2),
                bp.line(140,540,1076,540,1.2),plain(157,267,'陆侧 / 值机大厅',22),
                *[bp.rect(237+i*126,365,76,36,2) for i in range(6)],
                bp.path('M193 508H480V411M491 355V319H951',2.1,'none','stroke-dasharray="8 6" marker-end="url(#arrow)"'),
                plain(730,345,'行李输送',23),plain(166,566,'旅客流线',24)]
    if kind=='baggage':
        return [bp.rect(125,348,172,145,3),plain(147,433,'值机柜台',24),bp.rect(298,375,756,86,3),
                *[bp.line(x,376,x,460,1) for x in range(318,1054,28)],
                bp.rect(460,327,89,108,2.4,PAPER),bp.rect(476,346,35,32),plain(459,316,'测试箱',21),
                bp.path('M654 462V341H739V462',3),plain(636,322,'读码点',22),
                bp.path('M746 480H1011',2,'none','marker-end="url(#arrow)"')]
    if kind=='rack':
        return [bp.rect(171,223,244,380,3),
                *[bp.rect(191,246+47*i,204,34,1.6) for i in range(7)],
                bp.path('M418 411H560L620 358',1.7),bp.rect(620,265,433,250,2),
                plain(645,306,'ASSET  /  运维记录',22),plain(645,370,'设备编号与位置',24),
                plain(645,416,'旧设备 → 新设备',25),plain(645,467,'更换日期 / 复测结果',21)]
    if kind in ('terminal','steel'):
        a=[bp.path('M147 404L355 281H957L1074 404V557H147Z',3.2),
           bp.path('M147 404H1074M225 401L373 312H917L1008 401M147 532H1074',2)]
        for x in range(186,1060,110):
            a+=[bp.line(x,405,x,532,1.8)]
        if kind=='steel':
            for x in range(185,1000,110):a.append(bp.path(f'M{x} 405l110 127m0-127-110 127',1.1))
        else:
            a.append(bp.path('M527 531V460H702V531',1.9))
        return a+[bp.dim(146,598,1073,598),plain(450,625,'新航站楼 · 建筑轮廓示意',23)]
    raise KeyError(kind)

def sequence(items):
    outline=[]; detail=[]; labels=[]
    n=len(items)
    span=930/(n-1)
    for i,item in enumerate(items):
        x=160+i*span
        outline.append(bp.circle(x,385,24,2))
        detail.append(plain(x-9,393,str(i+1),21))
        labels.append(bp.text(x,454,item,23,align='middle'))
        if i<n-1: outline.append(bp.line(x+27,385,x+span-27,385,1.6,'marker-end="url(#arrow)"'))
    return outline,detail,labels

def chart():
    out=[bp.line(160,586,1090,586,2),bp.line(160,305,160,586,2)]
    for i,(yr,value) in enumerate([(2019,405),(2024,496),(2025,537)]):
        x=245+i*288
        height=round(value*.48)
        out.extend([bp.rect(x,586-height,139,height,2,'url(#hatchSparse)'),plain(x+12,564-height,str(value),33),plain(x+17,621,str(yr),20)])
    return out+[plain(160,266,'国际旅客吞吐量 / 万人次',25)]

KINDS={1:'ticket',2:'gate',4:'atoll',6:'terminal',8:'hall',9:'hall',10:'steel',11:'terminal',
       16:'terminal',17:'rack',20:'gate',23:'rack',25:'hall',27:'hall',28:'baggage',32:'baggage',33:'baggage',34:'baggage',36:'route',37:'rack',38:'terminal'}
FLOWS={
 5:('1960 首架飞机','1966 机场启用','1981 国际航站楼','2025 新航站楼'),
 15:('作业窗口重叠','暖通先吊装','弱电后进场'),
 18:('预计到达时间调整','原机位占用','复核替代机位'),
 19:('机型变更','检查机位尺寸','运行确认'),
 21:('机房 A','状态同步 / 复制','机房 B'),
 22:('A 侧服务中断','健康检查','B 侧接管'),
 29:('身份核验','授权通行','运行值守'),
 30:('单机测试','接口联调','全流程演练'),
 31:('机场','航空公司','地面服务','技术支持'),
 35:('新航站楼揭幕','首批航司转场','分批接续')
}

def draw_figure(i):
    if i==12:return bp.section()
    if i==13:return bp.node(False)
    if i==14:return bp.node(True)
    if i==24:return bp.service()
    if i==26:return bp.coverage()
    if i in FLOWS:
        outline,details,labels=sequence(FLOWS[i])
        return bp.layer(0,[bp.center(129,385,1131,385)])+bp.layer(1,outline)+bp.layer(2,details)+bp.layer(4,labels)
    outlines=chart() if i==7 else plan(KINDS[i])
    geometry=[item for item in outlines if not item.startswith('<text')]
    names=[item for item in outlines if item.startswith('<text')]
    pivot=math.ceil(len(geometry)/2)
    return (bp.layer(0,[bp.center(132,407,1110,407)])+bp.layer(1,geometry[:pivot])
          +bp.layer(2,geometry[pivot:])+bp.layer(4,names))

def plate(i,shot,drawing,caption):
    _,_,chapter,_,title,_=shot
    source={7:'统计：Maldives Bureau of Statistics',12:'依据建筑总剖面 05',13:'管综模型重绘',14:'同机位复核示意'}.get(i,'工程与运营原理示意')
    item=(f'{i:02d}',title,'VELANA TERMINAL 1',lambda:drawing,'',source,f'CH. {(base.OPEN,base.BUILD,base.IT,base.ORAT,base.OPS).index(chapter)+1}')
    svg=bp.sheet(item)
    # Reserve the lower strip for the sheet grid. Put subtitles in its notes column.
    a=svg.index('<rect x="104" y="699"')
    b=svg.index('<text x="1190" y="133"',a)
    svg=svg[:a]+svg[b:]
    x=svg.rindex('</svg>')
    grid=''.join(bp.text(119+x*112,772,chr(65+x),14,bp.INK) for x in range(9))
    block=bp.line(105,735,1125,735,.8)+grid
    subtitle=(bp.line(1190,349,1490,349,.8)+bp.text(1191,377,'NOTE  /  '+f'{i:02d}',18,bp.INK)
              +multiline(caption,12,1191,421,22,36))
    if i==14:
        subtitle+=('<g transform="rotate(-9 1340 580)"><rect x="1220" y="546" width="241" height="58" '
                   'rx="4" fill="none" stroke="#f08580" stroke-width="2"/>'
                   +bp.text(1340,584,'调整后复核',28,'#f08580','middle')+'</g>')
    return svg[:x]+block+subtitle+svg[x:]

def render_svg(svg,output):
    input_path=output.with_suffix('.svg')
    input_path.write_text(svg,encoding='utf-8')
    subprocess.run(['inkscape',str(input_path),f'--export-filename={output}','--export-width=1280'],
                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)

def map_frames(data,total):
    geo=json.loads((data/'world_land.geojson').read_text())
    local=json.loads((data/'local_geometry.json').read_text())
    world=[]
    for feature in geo['features']:
        g=feature['geometry']
        polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
        world.extend(poly[0] for poly in polys)
    rings=[(min(p[0] for p in land), max(p[0] for p in land), min(p[1] for p in land), max(p[1] for p in land),land) for land in world]
    lon,lat=73.52697,4.18454
    from PIL import ImageFont
    font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',21,index=2)
    for f in range(total):
        ratio=f/(total-1)
        easing=ratio*ratio*(3-2*ratio)
        # A single optical zoom over reprojected vectors. WGS84 vectors stay sharp.
        longitude_span=360*(.077/360)**easing
        latitude_center=lat+11*longitude_span/360
        longitude_center=lon-27*longitude_span/360
        xppu=1100/longitude_span
        def project(pt):
            x,y=pt
            return (round(490+(x-longitude_center)*xppu),round(365-(y-latitude_center)*xppu))
        image=Image.new('RGB',SIZE,'#0d1726')
        draw=ImageDraw.Draw(image)
        draw.rectangle((35,25,1243,694),fill='#1a3870',outline='#9cbdde',width=2)
        drawing=Image.new('RGB',(965,505),'#1e437e')
        d=ImageDraw.Draw(drawing)
        for x in range(5,960,44): d.line((x,0,x,505),fill='#31548b')
        for y in range(4,505,44):d.line((0,y,965,y),fill='#31548b')
        def xy(pt):
            x,y=project(pt)
            return (x-65,y-120)
        if longitude_span>1.1:
            bx=(longitude_center-longitude_span,longitude_center+longitude_span)
            by=(latitude_center-longitude_span,latitude_center+longitude_span)
            for lo,hi,bot,top,land in rings:
                if hi<bx[0] or lo>bx[1] or top<by[0] or bot>by[1]: continue
                d.polygon([xy(v) for v in land],fill='#31588e',outline='#93b9db',width=1)
        if longitude_span<4:
            for land in local['coast']:
                d.polygon([xy(v) for v in land],fill='#4774a6',outline='#c1ddf5',width=1)
            for runway in local['runway']:
                d.line([xy(v) for v in runway],fill='#c4e4ff',width=2)
            for terminal in local['terminal']:
                d.polygon([xy(v) for v in terminal],fill='#c3def6')
            if longitude_span<.21:
                for name,loc in [('马累',(73.50,4.178)),('胡鲁马累',(73.547,4.213))]:
                    x,y=xy(loc);d.text((x+7,y-22),name,font=font,fill='#dcecf7')
        x,y=xy((lon,lat))
        d.ellipse((x-13,y-13,x+13,y+13),outline='#e7f1fb',width=2)
        d.ellipse((x-3,y-3,x+3,y+3),fill='#e7f1fb')
        d.line((x+12,y,x+64,y+38,x+239,y+38),fill='#e7f1fb')
        d.text((x+67,y+9),'维拉娜国际机场',fill='#e7f1fb',font=font)
        image.paste(drawing,(65,120))
        draw.text((65,60),'FIG. 03   /   全球 → 南亚 → 胡鲁累岛',font=font,fill='#e7f1fb')
        draw.text((1054,153),'GENERAL NOTES',font=font,fill='#e7f1fb')
        draw.line((1048,196,1210,196),fill='#93b9db')
        draw.text((1054,222),'位置定位',font=font,fill='#e7f1fb')
        draw.text((1054,271),'印度洋 · 马尔代夫',font=font,fill='#e7f1fb')
        draw.text((66,649),'Natural Earth  /  © OpenStreetMap contributors',font=font,fill='#b4cbe1')
        yield image

def picture_frames(i,shot,workspace):
    phase_files=[]
    schematic=draw_figure(i)
    # Render each drafting stage separately so the reveal leaves the paper and title block fixed.
    for j,note in enumerate(shot[-1]):
        p=workspace/f'shot{i:02}-{j}.png'
        render_svg(plate(i,shot,schematic,note),p)
        phase_files.append(p)
    complete=[Image.open(p).convert('RGB') for p in phase_files]
    stages=[]
    for n in (0,1,2):
        root=ET.fromstring('<r xmlns="http://www.w3.org/2000/svg">'+schematic+'</r>')
        for parent in root.iter():
            for child in list(parent):
                stage=child.attrib.get('data-stage')
                if stage is not None and int(stage)>n:parent.remove(child)
        limited=''.join(ET.tostring(node,encoding='unicode') for node in root)
        p=workspace/f'layer{i:02}-{n}.png'
        render_svg(plate(i,shot,limited,shot[-1][0]),p)
        stages.append(Image.open(p).convert('RGB'))
    total=(shot[1]-shot[0])*FPS
    for j in range(total):
        time=j/FPS
        caption=min(len(complete)-1,j*len(complete)//total)
        if time<1.6:
            step=min(2,int(time/.42))
            left=stages[step]
            finish=stages[step+1] if step<2 else complete[caption]
            p=min(1,(time-step*.42)/.42)
            frame=left.copy()
            x=78+round(p*830)
            box=(78,146,max(79,x),558)
            frame.paste(finish.crop(box),box[:2])
            yield frame
        else:
            # Drift gently over the drawing pane without moving the notes.
            frame=complete[caption].copy()
            scene=frame.crop((66,149,930,551))
            p=(j/(total-1))
            z=1+.028*math.sin(math.pi*p)**2
            cx,cy=scene.width/2,scene.height/2
            if j%2==0 or time < 1.6+1/FPS:
                camera=scene.transform(scene.size,Image.Transform.EXTENT,
                       (cx-cx/z,cy-cy/z,cx+cx/z,cy+cy/z),resample=Image.Resampling.BICUBIC)
            frame.paste(camera,(66,149))
            yield frame

def render(args):
    shots=base.schedule(args.materials)
    assert len(shots)==38 and shots[-1][1]==360
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        d=Path(tmp)
        cuts=[]
        for i,shot in enumerate(shots,1):
            name=d/f'shot{i:02}.mp4'
            frames=map_frames(args.data,(shot[1]-shot[0])*FPS) if i==3 else picture_frames(i,shot,d)
            with subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','24','-i','-','-an',
                                   '-c:v','libx264','-threads','3','-preset','ultrafast','-crf','22','-pix_fmt','yuv420p',str(name)],stdin=subprocess.PIPE) as ff:
                for frame in frames:ff.stdin.write(frame.tobytes())
                ff.stdin.close()
                if ff.wait():raise RuntimeError(f'Shot {i} render failed')
            cuts.append(name)
            print(f'{i:02} / 38',flush=True)
        concat=d/'list.txt'
        concat.write_text(''.join(f"file '{p}'\n" for p in cuts))
        audio=d/'guide.wav'
        base.write_audio(audio,360,CHAPTERS[:-1])
        meta=d/'chapters.txt'
        meta.write_text(';FFMETADATA1\n'+''.join(f'[CHAPTER]\nTIMEBASE=1/1000\nSTART={a*1000}\nEND={b*1000}\ntitle={title}\n'
             for a,b,title in zip(CHAPTERS,CHAPTERS[1:],base.CHAPTERS)), encoding='utf-8')
        subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(concat),'-i',str(audio),'-i',str(meta),
                        '-map','0:v:0','-map','1:a:0','-map_metadata','2','-map_chapters','2','-c:v','copy','-c:a','aac','-b:a','112k','-movflags','+faststart',str(args.output)],check=True)

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--materials',type=Path,required=True)
    cli.add_argument('--data',type=Path,required=True)
    cli.add_argument('--output',type=Path,required=True)
    render(cli.parse_args())
