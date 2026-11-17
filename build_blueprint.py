"""Generate editable SVG source sheets for the Velana Blueprint animation."""
import argparse
import html
from pathlib import Path

W, H = 1600, 900
WHITE = '#e7f1fb'
INK = '#b7d3ec'

def line(x1,y1,x2,y2,w=1.8,extra=''):
    return f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{WHITE}" stroke-width="{w}" {extra}/>'
def path(d,w=2,fill='none',extra=''):
    return f'<path d="{d}" fill="{fill}" stroke="{WHITE}" stroke-width="{w}" {extra}/>'
def rect(x,y,w,h,weight=1.7,fill='none'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" stroke="{WHITE}" stroke-width="{weight}" fill="{fill}"/>'
def text(x,y,t,size=23,color=WHITE,align='start'):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" text-anchor="{align}">{html.escape(t)}</text>'
def circle(x,y,r,w=1.4):
    return f'<circle cx="{x}" cy="{y}" r="{r}" stroke="{WHITE}" stroke-width="{w}" fill="none"/>'
def center(x1,y1,x2,y2):
    return line(x1,y1,x2,y2,1,'class="axis" stroke-dasharray="13 4 2 4" opacity=".48"')
def dim(x,y,xx,yy):
    return line(x,y,xx,yy,1,'marker-start="url(#arrow)" marker-end="url(#arrow)"')
def balloon(x,y,xx,yy,n,t):
    return (line(x,y,xx-16,yy,.95)+circle(xx,yy,16)+
            text(xx,yy+5,str(n),14,align='middle')+text(xx+26,yy+6,t,17))
def layer(stage, parts):
    return f'<g data-stage="{stage}">'+''.join(parts)+'</g>'

def section():
    floors=[(280,'+21.700'),(329,'+18.000'),(389,'+12.300'),(471,'+6.000'),(556,'±0.000'),(601,'−3.000')]
    grids=[166,266,375,487,601,721,826,945,1058,1143]
    roof='M155 329H442L483 340L711 323L741 280L901 335V389L1145 402V413L901 400V346L742 293L718 334L483 351L442 341H155Z'
    a=[center(126,y,1152,y) for y,_ in floors]+[center(x,305,x,618) for x in grids]
    b=[path(roof,3.1),path('M155 341V556H1145V398',3.1),
       path('M165 471H257L354 389H900M165 482H261L358 400H900',2.6),
       path('M357 471H1120V482H357ZM328 389H901M155 556H1145V567H155Z',2.5),
       path('M146 601H1145',1.6)]
    c=[]
    for x in grids[1:-1]:
        y=400 if x>890 else 350
        c.append(rect(x,y,6,556-y,1.2))
    c += [path('M167 545H200V472H168ZM737 544H792V483H737ZM836 544H867V483H836Z',1.4),
          path('M394 482V540H473V482M511 482V540H560V482M806 393V466H863V393',1.25),
          path('M885 471H1082V482H885Z',1.2),
          text(514,453,'候机区',17),text(623,379,'到达通廊',17),text(971,531,'值机大厅',19),
          rect(162,567,980,34,0,'url(#hatch)')]
    d=[dim(117,280,117,556)]
    for y,lab in floors:
        d.extend([line(117,y,126,y,.8),text(101,y+5,lab,11,align='end')])
    for x,l in zip(grids,'ABCDEFGHIJ'):
        d.extend([circle(x,630,12),text(x,635,l,13,align='middle')])
    e=[balloon(980,487,1010,220,1,'吊顶节点')]
    return ''.join([layer(0,a),layer(1,b),layer(2,c),layer(3,d),layer(4,e)])

def node(adjusted):
    # Oblique projection from the coordination model: duct along x; tray along y.
    def pt(x,y,z): return (round(570+56*x+34*y),round(460+19*x-29*y-46*z))
    def pp(coords,w=1.8,fill='none'):
        p=[pt(*v) for v in coords]
        return path('M'+'L'.join(f'{x} {y}' for x,y in p),w,fill)
    def shape(coords,w=1.9,fill='#204782'):
        p=[pt(*v) for v in coords]
        return path('M'+'L'.join(f'{x} {y}' for x,y in p)+'Z',w,fill)
    def duct():
        x0,x1,y0,y1,z0,z1=-6,6,-.7,.7,1.85,2.75
        return [shape([(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],2.8),
                shape([(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)],2.6),
                shape([(x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1)],2.4)]
    def tray(a,b,z):
        v=[pp([(x,a,z),(x,b,z)],2.9) for x in (-.45,.45)]
        for i in range(1,15):
            y=a+(b-a)*i/15
            v.append(pp([(-.45,y,z),(.45,y,z)],1.25))
        return v
    z=1.22 if adjusted else 2.28
    axis=[center(210,545,1023,389),center(396,173,762,599),center(573,190,573,560)]
    structure=[pp([(-6.5,-3.7,4.1),(6.4,-3.7,4.1),(6.4,3.8,4.1),(-6.5,3.8,4.1),(-6.5,-3.7,4.1)],2.2)]
    for x in [-5,-2.5,2.5,5]:
        structure+= [pp([(x,-3.7,4.1),(x,3.8,4.1)],1.1),pp([(x,-.8,4.1),(x,-.8,1.79),(x,.8,1.79),(x,.8,4.1)],1.1)]
    if adjusted:
        outlines=structure+tray(.68,4,z)+duct()+tray(-4,.68,z)
    else:
        outlines=structure+tray(.7,4,z)+duct()+tray(-4,-.7,z)
    details=[]
    for y in [-3.2,-1.6,1.8,3.2]:
        details.append(pp([(-.53,y,4.1),(-.53,y,z-.10),(.53,y,z-.10),(.53,y,4.1)],1))
    if not adjusted:
        for x in [-.45,.45]:
            a,b=pt(x,-.7,z),pt(x,.7,z)
            details.append(line(*a,*b,2,'stroke-dasharray="5 5"'))
        x,y=pt(0,0,2.35)
        details.append(circle(x,y,49,2))
    else:
        x,y=pt(0,0,z)
    dx,dy=pt(.72,-.73,1.85); ex,ey=pt(.72,-.73,z)
    dims=[dim(dx+20,dy,ex+20,ey),text(171,618,'同一视向 · 相对标高示意',18,INK)]
    if adjusted:
        dims += [text(dx+32,(dy+ey)/2+6,'净空待复核',16)]
    tags=[balloon(*pt(3.65,.1,2.74),805,232,1,'暖通风管'),
          balloon(*pt(.3,-3.55,z),279,540,2,'弱电梯架'),
          balloon(x,y,810,555,3,'复核位置' if adjusted else '几何相交')]
    return '<g transform="translate(100 139) scale(.86 .82)">'+''.join([layer(0,axis),layer(1,outlines),layer(2,details),layer(3,dims),layer(4,tags)])+'</g>'

def service():
    c=[center(138,478,1128,478)]
    outline=[]
    detail=[]
    for x,title,sub in [(177,'资源管理','机位 / 登机口'),(449,'AODB','运行数据发布'),(770,'FIDS','航显 / B06'),(770,'PA','广播 / 分区')]:
        y=536 if title=='PA' else 393
        outline += [rect(x,y,188,77,2.2,'#214982')]
        detail += [text(x+11,y+29,title,23),text(x+11,y+54,sub,15)]
    detail += [line(365,431,448,431,2,'marker-end="url(#arrow)"'),
               path('M637 431H769M700 431V574H769',2,'none','marker-end="url(#arrow)"')]
    for x,t in [(201,'机房 A'),(452,'机房 B')]:
        outline.append(rect(x,232,179,63,1.5))
        detail.append(text(x+20,271,t,21))
    detail += [line(380,264,450,264,1.7,'marker-end="url(#arrow)"'),text(670,264,'数据复制 / 服务接管',18,INK)]
    return layer(0,c)+layer(1,outline)+layer(2,detail)+layer(4,[balloon(632,432,838,348,1,'变更已确认')])

def coverage():
    axes=[center(165,405,1115,405),center(640,204,640,629)]
    p=[rect(183,232,882,335,2.6),rect(203,251,842,298,1.5,'url(#hatchSparse)')]
    detail=[]
    for y in [331,473]:
        for x in range(295,1010,140):
            detail+=[circle(x,y,9,2.3),circle(x,y,15,.8)]
    d=[dim(185,203,1065,203),text(622,193,'候机区平面 · 覆盖示意',19,INK,align='middle')]
    tags=[balloon(995,331,1074,291,1,'扬声器'),balloon(402,474,311,624,2,'连续区域'),text(713,622,'示意线 · 无声压级数值',18,INK)]
    return layer(0,axes)+layer(1,p)+layer(2,detail)+layer(3,d)+layer(4,tags)

SCENES=[
 ('01','航站楼总剖面','SECTION 05',section,'总剖面把值机大厅、候机区和到达通廊放到同一张图上。','据建筑总剖面 05 简化描绘','POSITION'),
 ('02','吊顶管综｜检查状态','CLASH STUDY',lambda:node(False),'检查位置：梯架路径穿入风管占用的空间。','据管综示意模型重新投影','CHECK'),
 ('03','吊顶管综｜标高调整','REVISION A',lambda:node(True),'调整桥架标高后，从风管下方通过，保留净空复核。','按同一视向重新投影','REVIEW'),
 ('04','航班变更｜信息发布','SERVICE FLOW',service,'确认后的登机口变更，通过 AODB 发布给航显等业务系统。','业务关系为原理示意','FLOW'),
 ('05','候机区｜广播布点','PA COVERAGE',coverage,'两排扬声器覆盖候机区，中央区域连续覆盖。','平面示意，未给出实测声压','COVERAGE'),
]

def sheet(scene):
    n,title,en,drawing,note,source,status=scene
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="{title}">
<defs>
 <linearGradient id="paper" x2=".84" y2="1"><stop stop-color="#142b60"/><stop offset=".49" stop-color="#284c89"/><stop offset="1" stop-color="#15356e"/></linearGradient>
 <pattern id="hatch" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path d="M0 0V10" opacity=".41" stroke="{WHITE}"/></pattern>
 <pattern id="hatchSparse" width="16" height="16" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path d="M0 0V16" opacity=".21" stroke="{WHITE}"/></pattern>
 <marker id="arrow" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto-start-reverse"><path d="M0 0L6 3L0 6" fill="none" stroke="{WHITE}" stroke-width="1"/></marker>
 <filter id="fiber" x="0%" y="0%" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".06 .39" numOctaves="3" seed="8" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter>
</defs>
<style>text{{font-family:"Noto Sans CJK SC","Microsoft YaHei",sans-serif;letter-spacing:1px}} .paper-noise{{mix-blend-mode:soft-light}} @media(prefers-reduced-motion: reduce){{*{{animation:none!important}}}}</style>
<rect width="1600" height="900" fill="#0c121c"/><rect x="51" y="42" width="1505" height="820" rx="2" fill="#070d19"/>
<rect x="45" y="35" width="1505" height="820" rx="2" fill="url(#paper)"/>
<rect class="paper-noise" x="45" y="35" width="1505" height="820" opacity=".16" filter="url(#fiber)"/>
<path d="M1000 36L1003 854" stroke="#aec4ea" opacity=".12" stroke-width="3"/><path d="M996 36V855" stroke="#0a1a3c" opacity=".21" stroke-width="3"/>
{rect(72,59,1450,770,1.45)}{rect(78,65,1438,758,.65)}
{text(103,109,'VELANA INTERNATIONAL AIRPORT  /  TERMINAL DEVELOPMENT',19,INK)}
{text(102,161,title,43)}{text(1128,128,'FIG. '+n,35,align='end')}
{line(102,181,1135,181,.9)}{line(1170,90,1170,795,.85)}
<g id="figure">{drawing()}</g>
{rect(104,699,1029,90,1.2,'#1b396f')}{rect(111,706,1015,76,.58)}
{line(215,707,215,781,.85)}{text(130,744,'NOTE',18,INK)}{text(130,766,n,17)}
{layer(5,[text(238,754,note,25)])}
{text(1190,133,'GENERAL NOTES',20)}{line(1191,151,1492,151,.8)}
{layer(5,[text(1191,192,'项目   /   新航站楼',18),text(1191,231,'基础   /   '+source,17),text(1191,271,'图形   /   影视重绘',17),text(1191,311,'比例   /   示意',17)])}
{rect(1189,635,301,153,1.4)}{line(1190,677,1490,677,.8)}{line(1190,732,1490,732,.8)}
{text(1204,664,'DRAWING  /  VELANA T1',17)}{text(1204,710,en,21)}
{text(1204,762,n+'   /   '+status,21)}
</svg>'''

PAGE = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>维拉娜机场｜Blueprint</title>
<style>body{margin:0;background:#0c121c;color:#e7f1fb;font:16px system-ui,sans-serif}main{max-width:1280px;margin:auto}object{display:block;width:100%;aspect-ratio:16/9}nav{display:flex;flex-wrap:wrap;gap:.55em;padding:12px 20px}button{color:inherit;background:#173464;border:1px solid #7ea5db;border-radius:2px;padding:.55em .8em;cursor:pointer}button[aria-pressed=true]{background:#e7f1fb;color:#142b60}</style>
<main><nav id="nav" aria-label="图纸"></nav><object id="preview" type="image/svg+xml" aria-label="蓝图动画"></object></main>
<script>
const labels=["总剖面","硬碰撞","标高调整","信息发布","广播覆盖"];
const screen=document.getElementById("preview"), nav=document.getElementById("nav");
let animations=[];
function replay(){
 animations.forEach(a=>a.cancel()); animations=[];
 const doc=screen.contentDocument;
 if(!doc||matchMedia("(prefers-reduced-motion: reduce)").matches)return;
 for(const layer of doc.querySelectorAll("[data-stage]")){
   const stage=Number(layer.dataset.stage), delay=stage*290;
   for(const p of layer.querySelectorAll("path,rect,circle")){
      const length=p.getTotalLength(); 
      if(p.hasAttribute("stroke-dasharray")||!length){
        animations.push(p.animate([{opacity:0},{opacity:1}],{duration:350,delay,fill:"both"}));continue;
      }
      animations.push(p.animate([{strokeDasharray:length,strokeDashoffset:length,opacity:0},{strokeDasharray:length,strokeDashoffset:0,opacity:1}],{duration:850,delay,fill:"both"}));
   }
   for(const p of layer.querySelectorAll("text"))
     animations.push(p.animate([{opacity:0},{opacity:1}],{duration:350,delay:delay+470,fill:"both"}));
 }
}
screen.addEventListener("load",replay);
for(const [i,label] of labels.entries()){
 const b=document.createElement("button");b.textContent=label;b.setAttribute("aria-pressed",String(i===0));
 b.onclick=()=>{for(const t of nav.querySelectorAll("[aria-pressed]"))t.setAttribute("aria-pressed",String(t===b));screen.data="fig-0"+(i+1)+".svg";};nav.append(b);
}
const r=document.createElement("button");r.textContent="重播绘线";r.onclick=replay;nav.append(r);
screen.data="fig-01.svg";
</script></html>'''

def main(output):
    output.mkdir(parents=True,exist_ok=True)
    for scene in SCENES:
        (output/f'fig-{scene[0]}.svg').write_text(sheet(scene), encoding='utf-8')
    (output/'index.html').write_text(PAGE,encoding='utf-8')
    (output/'README.md').write_text(
        '# 维拉娜机场 Blueprint 素材\n\n'
        '在本目录运行 `python -m http.server 8000`，然后打开 `http://localhost:8000` 浏览和重播绘线。'
        '也可用支持 SVG 的矢量工具直接编辑各图。各图以 data-stage 分组，依次为中心线、轮廓、细节、尺寸、引线、图注。\n\n'
        '总剖面参照建筑总剖面 05 手动简化，层高按原图示标高，并非等比例施工图。'
        '管综两图按示意模型的同一视向重投影。信息发布及广播覆盖为原理示意。\n',
        encoding='utf-8')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path,nargs='?',default=Path('Velana_Blueprint'))
    main(parser.parse_args().output)
