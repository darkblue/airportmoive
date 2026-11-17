"""Assemble the six-minute Velana terminal film from the production media pack."""
import argparse
import csv
import math
import subprocess
import tempfile
import wave
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H, FPS = 1280, 720, 24
CHAPTERS = ('为什么扩建', '从图纸到现场', '让航站楼运转', '投运前的演练', '投入运营')
OPEN, BUILD, IT, ORAT, OPS = ('01_Opening', '02_Construction', '03_ELV_IT', '04_ORAT_Transfer', '05_Operations')
TEAL, WHITE, MUTED, INK = '#65d8cb', '#f0f5f6', '#a8bfca', '#091e2b'

# Shot number, source assets, in-frame title, and editorial subtitles.
# A vertical bar in the source list separates panels. @ denotes a generated shot.
SHOTS = [
    (OPEN+'/Opening_Prop_B04.png', '原登机口 B04', ['登机牌上的登机口是 B04。']),
    ('@gate', '登机口变更', ['走到岔路口，航显已经更新为 B06。']),
    (OPEN+'/Map_World.png|'+OPEN+'/Map_South_Asia.png|'+OPEN+'/VIA_Overall_Aerial_TMA_Reference.png', '从世界地图到胡鲁累岛', ['从印度洋上的马尔代夫群岛，找到维拉娜国际机场。']),
    (OPEN+'/Maldives_Coral_Island.jpg', '马尔代夫群岛', ['许多人的海岛行程，从这座机场开始。']),
    (OPEN+'/History_Timeline.png', '机场的早期历史', ['1960 年，首架飞机在胡鲁累降落。1966 年，机场正式启用。']),
    (OPEN+'/Old_Terminal_2010.jpg|'+OPEN+'/T1_Exterior_Mihaaru.jpg', '从旧航站楼到新航站楼', ['随着客流增长，值机、安检和候机都需要更多空间。']),
    (OPEN+'/International_Passengers.png', '国际航班旅客吞吐量', ['统计口径包括国际航班到达和出发旅客。', '几班飞机集中抵达时，柜台、通道和转盘都要承接客流。']),
    (BUILD+'/T1_Checkin_Mihaaru.jpg|'+OPEN+'/T1_Carousel_Mihaaru.jpg', '值机大厅与行李提取', ['扩建从梳理旅客和行李的路线开始。']),
    (BUILD+'/Drawings/Design_Ground_Floor_L0.png|'+BUILD+'/T1_Checkin_Mihaaru.jpg', '平面图上的旅客与行李流线', ['业主 MACL 提出使用需求，设计团队把流程落实到楼层和空间。', '值机柜台面向旅客，后方接入行李输送线。']),
    (BUILD+'/T1_Site_Visit_Presidency.jpg', '主体结构与专业施工', ['建设由中国交建体系下的中国港湾参建，中交二公局参与施工。', '主体、钢结构和屋面推进时，各专业也在协调设备与管线接口。']),
    (BUILD+'/Drawings/Design_Axonometric_Section.png|'+BUILD+'/T1_Checkin_Mihaaru.jpg', '建筑轴测与完工大厅', ['可见的是大厅。吊顶里还要布置风管、消防管和弱电桥架。']),
    (BUILD+'/Drawings/Velana_Cross_Section_05.png', '建筑总剖面 05', ['总剖面交代大厅的高度、楼层关系与吊顶位置。', '切到三维模型，可以看到管线之间的空间关系。']),
    ('@before', '风管与弱电桥架相交', ['模型会审发现，风管和弱电桥架占用了同一空间。', '暖通和弱电团队在安装前协调路线。']),
    ('@compare', '调整标高前后｜同一机位', ['调整标高后，桥架从风管下方通过。', '复核还要考虑桥架容量、敷缆和检修所需的净空。']),
    ('@schedule', 'BIM 4D｜安装顺序协调', ['完工位置可以错开，吊装与桥架作业仍可能在同一时段占用同一作业区。', '4D 模型结合施工计划，提前协调吊装、进场和桥架安装顺序。']),
    ('@after', '竣工模型与 LOD 500', ['本项目要求 BIM 交付达到 LOD 500。', '竣工阶段核对现场安装，把设备位置和属性纳入交付资料。']),
    (OPS+'/LOD500_Asset_Record.png', '竣工交付｜模型和资产信息', ['模型中的设备可以关联编号、位置及维护资料。', '这套信息随后交给接管航站楼的运维团队。']),
    (IT+'/Gate_Change.png', '预计到达时间变化', ['预计到达时间提前或推迟，原定机位可能仍被占用。']),
    ('@aircraft', '机型变更｜机位适配', ['航司更换机型时，运行人员还要复核机位适配和资源占用。']),
    ('@gate', '运行人员确认资源调整', ['资源管理系统提示冲突，由运行人员确认调整。', '如果新机位对应另一登机口，B04 可能改为 B06。']),
    (IT+'/Dual_Server_Rooms.png', '双机房｜数据复制', ['机房和网络汇聚航站楼各区域的业务连接。', '双机房高可用依赖数据复制、状态检查和接管机制。']),
    ('@failover', '双机房｜业务接管示意', ['一侧服务中断时，系统按预定策略切换。', '接管前还要确认数据状态，避免两边同时对外写入。']),
    (IT+'/Dual_Server_Rooms.png', '双机房｜恢复与验证', ['恢复时核对数据、业务入口和告警记录。', '切换与回切都需要测试。']),
    (IT+'/AODB_Service_Outputs.png', 'AODB｜发布已确认的变更', ['机场运行数据库发布确认后的航班和资源信息。', '航显更新登机口，地服岗位据此组织现场服务。']),
    (IT+'/T1_Lounge_Mihaaru.jpg', '公共广播｜候机区提示', ['公共广播按运行流程，向候机区旅客发布登机口变更。']),
    (IT+'/Velana_Broadcast_Coverage_2D.png', '公共广播｜二维声场覆盖', ['分区布置扬声器时，设计团队通过声学模拟核对覆盖与语言清晰度。', '噪声探测器采集背景噪声，广播系统在设定范围内调整分区增益。']),
    (BUILD+'/T1_Checkin_Mihaaru.jpg', 'COMMON USE（多主机）', ['共用值机平台让不同航司在同一组柜台使用各自的业务应用。']),
    (ORAT+'/CheckIn_Baggage_Closeup.png', '值机柜台与行李输送', ['行李贴签后从柜台背面进入输送线，后续经过扫描和核对。']),
    ('@access', '门禁与运行值守', ['门禁管理人员通行，运行岗位监测相关告警和设备状态。']),
    ('@orattest', '从单机验收到全流程演练', ['设备安装并测试后，各方进行接口联调、岗位培训和流程演练。']),
    (ORAT+'/ORAT_Checkin_MACL.jpg', 'ORAT｜运行准备与转场', ['ORAT 把机场、航司、地服及技术团队放在同一套运行场景里验证。']),
    (ORAT+'/Baggage_ORAT_Demo.png', '模拟演练｜测试箱读码失败', ['演练中的一只测试箱未能读出条码，按流程转入人工处理。']),
    (ORAT+'/CheckIn_Baggage_Closeup.png', '模拟演练｜核对并补签', ['岗位人员核对行李记录，重新贴签，并送回指定扫描点。']),
    (ORAT+'/Baggage_ORAT_Demo.png', '模拟演练｜复扫与恢复', ['复扫通过后，演练组核对处置时间和记录，验证流程能否恢复。']),
    (ORAT+'/T1_Inauguration_Presidency.jpeg|'+ORAT+'/Terminal_Transfer_Timeline.png', '新航站楼启用与航司转场', ['新航站楼于 2025 年 7 月揭幕。', '航司分阶段转入新楼，每批转场前后都要衔接服务和人员。']),
    (OPS+'/T1_Aerobridge_Mihaaru.jpg', '旅客抵达 B06', ['航显、广播和岗位信息对上了，旅客循着指引走到新的登机口。']),
    (OPS+'/LOD500_Asset_Record.png', '运维交接｜设备更换记录', ['运维团队按位置和编号找到设备。', '发生更换时，资产台账记录更换时间、设备信息和维护结果。']),
    (OPEN+'/T1_Exterior_Mihaaru.jpg', '维拉娜国际机场', ['从一张图纸到一次顺利登机。', '航站楼接续每一段旅程，连接马尔代夫与世界。']),
]

FLOW = {
    '@gate': (['B04', 'B06'], ['原登机口', '新登机口'], '演示界面 · 模拟航班'),
    '@schedule': (['作业窗口重叠', '暖通先吊装', '弱电进场安装'], ['同一区域', '弱电先做邻区', '吊装设备撤离后'], 'BIM 4D · 施工组织示意'),
    '@aircraft': (['机型变更', '复核适配', '确认资源'], ['航司信息', '机位尺寸和占用', '运行人员'], '运行处置 · 流程示意'),
    '@failover': (['A 机房', '健康检查', 'B 机房'], ['业务中断', '核对状态', '按策略接管'], '高可用 · 原理示意'),
    '@access': (['身份核验', '授权通行', '运行值守'], ['刷卡识别', '门禁控制', '告警处置'], '门禁 · 流程示意'),
    '@orattest': (['单机测试', '接口联调', '全流程演练'], ['核对设备功能', '验证系统交换', '验证岗位协作'], 'ORAT · 运行准备'),
}

def seconds(stamp):
    minute, second = map(int, stamp.split(':'))
    return minute * 60 + second


def timecode(seconds, srt=False):
    minute, second = divmod(seconds, 60)
    return f'00:{minute:02d}:{second:02d},000' if srt else f'{minute:02d}:{second:02d}'


def schedule(materials):
    with (materials / '00_Index/Shot_Asset_Index_38.csv').open(encoding='utf-8-sig') as f:
        index = list(csv.DictReader(f))
    return [(seconds(row['开始']), seconds(row['结束']), row['幕'], *shot)
            for row, shot in zip(index, SHOTS, strict=True)]


def source_labels(materials):
    with (materials / '00_Index/Sources_and_Rights.csv').open(encoding='utf-8-sig') as f:
        return {row['文件']: row['来源或作者'] for row in csv.DictReader(f) if row['文件']}


def make_frame_factory(materials, bim, fonts):
    credits = source_labels(materials)

    @lru_cache(maxsize=36)
    def font(size, bold=True):
        name = 'Bold' if bold else 'Regular'
        return ImageFont.truetype(str(fonts / f'NotoSansCJK-{name}.ttc'), size, index=2)

    def write(draw, pos, text, size, color=WHITE, bold=True, anchor='la'):
        draw.text(pos, text, fill=color, font=font(size, bold), anchor=anchor)

    @lru_cache(maxsize=32)
    def full_image(path, max_w, max_h):
        with Image.open(path) as img:
            return ImageOps.contain(img.convert('RGB'), (max_w, max_h), Image.Resampling.LANCZOS)

    def panel(canvas, ref, box, model=False):
        x, y, w, h = box
        path = bim / ref if model else materials / ref
        img = full_image(path, w, h)
        canvas.paste(img, (x + (w - img.width) // 2, y + (h - img.height) // 2))

    def frame(shotnum, shot, part, mode):
        start, end, chapter, ref, title, lines = shot
        chapter_index = (OPEN, BUILD, IT, ORAT, OPS).index(chapter)
        is_flow = ref in FLOW
        is_model = ref in ('@before', '@after', '@compare')
        is_blueprint = '/Drawings/' in ref or is_model
        base = '#112939' if is_blueprint else INK
        im = Image.new('RGB', (W, H), base)
        draw = ImageDraw.Draw(im)
        write(draw, (42, 21), 'VELANA INTERNATIONAL AIRPORT', 17, TEAL)
        write(draw, (1238, 21), CHAPTERS[chapter_index], 19, MUTED, anchor='ra')
        write(draw, (41, 52), title, 36)
        draw.line((42, 106, 1238, 106), fill='#325567', width=2)
        if is_flow:
            labels, notes, credit = FLOW[ref]
            n = len(labels)
            gap = 30
            card_w = (1160 - (n - 1) * gap) // n
            for i, (label, note) in enumerate(zip(labels, notes)):
                x = 60 + i * (card_w + gap)
                on = i <= mode
                draw.rounded_rectangle((x, 228, x + card_w, 439), 10, fill='#18394a',
                                       outline=TEAL if on else '#3a5868', width=3)
                draw.rectangle((x+16, 246, x+46, 251), fill=TEAL if on else '#526d7a')
                write(draw, (x + 22, 283), label, 33, WHITE if on else MUTED)
                write(draw, (x + 22, 362), note, 23, MUTED, False)
                if i + 1 < n:
                    write(draw, (x + card_w + gap//2, 310), '›', 30, TEAL, anchor='ma')
        elif ref == '@compare':
            for x, file, label in ((42, 'Clash.png', '检查状态'), (650, 'Resolved.png', '调整后')):
                write(draw, (x+2, 116), label, 20, TEAL)
                panel(im, file, (x, 148, 588, 425), True)
            credit = 'BIM 节点 · 同机位模型示意'
        elif is_model:
            panel(im, 'Clash.png' if ref == '@before' else 'Resolved.png', (43, 117, 1194, 465), True)
            credit = 'BIM 节点 · 模型示意'
        else:
            variants = ref.split('|')
            selected = variants[mode]
            if shotnum in (6, 8, 9, 11) and len(variants) == 2:
                for i, path in enumerate(variants):
                    x = 42 + i * 607
                    panel(im, path, (x, 135, 590, 427))
                    cap = credits.get(path, '项目建筑报告' if '/Drawings/' in path else '')
                    write(draw, (x, 573), cap, 15, MUTED, False)
                credit = '项目素材 · 双画面对照'
            else:
                panel(im, selected, (42, 119, 1196, 463))
                credit = credits.get(selected)
                if not credit:
                    if shotnum == 3:
                        credit = '底图：Natural Earth'
                    elif shotnum == 7:
                        credit = '统计来源：Maldives Bureau of Statistics'
                    elif shotnum == 5:
                        credit = '历史资料：MACL'
                    elif '/Drawings/' in selected:
                        credit = '项目建筑报告 / 总剖面图'
                    elif shotnum == 35:
                        credit = '转场依据：The Edition / MM News'
                    else:
                        credit = '项目制作素材 · 演示图'
        draw.line((42, 598, 1238, 598), fill='#325567', width=1)
        write(draw, (42, 608), credit, 15, MUTED, False)
        write(draw, (1238, 608), f'{shotnum:02d} / {len(SHOTS)}', 15, MUTED, anchor='ra')
        write(draw, (42, 647), lines[part], 26)
        return im

    return frame


def write_audio(path, duration, starts):
    rate = 24000
    t = np.arange(duration * rate, dtype=np.float32) / rate
    ambient = .013 * np.sin(t * (2 * np.pi * 110)) + .008 * np.sin(t * (2 * np.pi * 164.81))
    ambient *= .54 + .46 * np.sin(t * .26) ** 2
    for start in starts:
        count = min(rate // 2, len(t) - start * rate)
        u = np.arange(count, dtype=np.float32) / rate
        tone = .041 * np.sin(2 * np.pi * 330 * u) * np.exp(-u * 12) * np.minimum(1, u * 160)
        ambient[start * rate:start * rate + count] += tone
    for start in (3, 216, 312):
        u = np.arange(rate, dtype=np.float32) / rate
        for shift, freq in ((0, 660), (.24, 880)):
            v = np.maximum(0, u - shift)
            ambient[start*rate:(start+1)*rate] += .028 * np.sin(2*np.pi*freq*v) * np.exp(-v*8) * np.minimum(1,v*125)
    ambient *= np.minimum(1, np.minimum(t, duration - t) / 1.5)
    with wave.open(str(path), 'wb') as wav:
        wav.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
        wav.writeframes((np.clip(ambient, -1, 1) * 32767).astype('<i2').tobytes())


def render(args, editorial=False):
    shots = schedule(args.materials)
    if len(shots) != 38 or shots[-1][1] != 360 or any(a[1] != b[0] for a, b in zip(shots, shots[1:])):
        raise ValueError('Expected 38 continuous shots covering six minutes.')
    frame = make_frame_factory(args.materials, args.bim, args.fonts)
    chapters = [0, 45, 140, 265, 325, 360]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        audio = work / 'sound.wav'
        write_audio(audio, 360, chapters[:-1])
        metadata = work / 'chapter.ffmeta'
        metadata.write_text(';FFMETADATA1\n' + ''.join(
            f'[CHAPTER]\nTIMEBASE=1/1000\nSTART={s*1000}\nEND={e*1000}\ntitle={name}\n'
            for s,e,name in zip(chapters, chapters[1:], CHAPTERS)), encoding='utf-8')
        listfile = work / 'shots.txt'
        paths = []
        for number, shot in enumerate(shots, 1):
            start, stop, _, ref, _, lines = shot
            nframes = (stop-start)*FPS
            flow_count = len(FLOW[ref][0]) if ref in FLOW else len(ref.split('|'))
            grouped = number in (6, 8, 9, 11)
            # Separate assets and the corresponding caption changes at editable cuts.
            mode_cuts = {math.ceil(i*nframes/flow_count) for i in range(flow_count)} if not grouped else {0}
            line_cuts = {math.ceil(i*nframes/len(lines)) for i in range(len(lines))}
            boundaries = sorted(mode_cuts | line_cuts | {nframes})
            for j, (a,b) in enumerate(zip(boundaries, boundaries[1:])):
                mode = min(flow_count-1, a*flow_count//nframes) if not grouped else 0
                part = min(len(lines)-1, a*len(lines)//nframes)
                image = work / 'slide.png'
                frame(number, shot, part, mode).save(image)
                partfile = work / f'part-{number:02d}-{j}.mp4'
                progress = f'drawbox=x=43:y=706:w={int(1194*stop/360)}:h=3:color=0x65d8cb:t=fill'
                if editorial and number in (4, 10, 25, 27, 31, 38):
                    motion = (
                        "[0:v]split=2[plate][asset];"
                        "[asset]crop=1280:608:0:0,"
                        f"zoompan=z='1+0.035*min(on/{max(1,b-a-1)},1)':"
                        "x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1280x608:fps=24[window];"
                        "[plate][window]overlay=0:0"
                    )
                    kwargs = ['-filter_complex_threads', '1', '-filter_complex', motion]
                elif editorial:
                    kwargs = []
                elif number in (3, 4, 10, 25, 31, 36, 38):
                    # Move only the image region. The extended canvas preserves the
                    # full image and keeps source labels and subtitles fixed.
                    bg = '0x091e2b'
                    motion = (
                        "[0:v]split=2[plate][asset];"
                        "[asset]crop=1196:464:42:118,pad=1268:492:36:14:" + bg + ","
                        f"zoompan=z='1+0.055*min(on/{max(1,b-a-1)},1)':"
                        "x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1196x464:fps=24[window];"
                        f"[plate][window]overlay=42:118,{progress}"
                    )
                    kwargs = ['-filter_complex_threads', '1', '-filter_complex', motion]
                else:
                    kwargs = ['-vf', progress]
                subprocess.run(['ffmpeg', '-v', 'error', '-y','-loop','1','-framerate',str(FPS),'-i',str(image),
                                *kwargs,'-frames:v',str(b-a),'-c:v','libx264','-preset','veryfast' if editorial else 'ultrafast',
                                '-crf','19','-threads','3','-pix_fmt','yuv420p',str(partfile)],check=True)
                paths.append(partfile)
            print(f'{number:02d} / 38  {timecode(stop)}', flush=True)
        listfile.write_text(''.join(f"file '{p}'\n" for p in paths))
        subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(listfile),
                        '-i',str(audio),'-i',str(metadata),'-map','0:v:0','-map','1:a:0',
                        '-map_metadata','2','-map_chapters','2','-c:v','copy','-c:a','aac',
                        '-b:a','112k','-movflags','+faststart',str(args.output)],check=True)


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--materials', type=Path, required=True)
    cli.add_argument('--bim', type=Path, required=True)
    cli.add_argument('--fonts', type=Path, default=Path('/usr/share/fonts/opentype/noto'))
    cli.add_argument('--output', type=Path, default=Path('output/Velana_Full_Rough_Cut.mp4'))
    render(cli.parse_args())
