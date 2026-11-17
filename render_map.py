"""Render three Blueprint map plates and a 12-second camera sequence."""
import html
import json
import math
import subprocess
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parent
W,H=1600,900
AIRPORT=(73.5292,4.1918)
PALETTE=('#102750','#193c71','#afd0ec','#e9f3fb')
VIEWS=[
    ('01','世界定位','WORLD',(-181,-66,181,84),[('欧洲',(13,47),-18,-19),('非洲',(20,10),-20,-20),('亚洲',(104,42),-20,-20),('印度洋',(78,-28),-20,0)]),
    ('02','南亚与印度洋','SOUTH ASIA',(47,-12,102,26),[('印度',(78,17),-18,-25),('斯里兰卡',(80.6,7.8),18,-9),('印度洋',(62,-5),-30,0)]),
    ('03','马累与胡鲁累岛','HULHULÉ',(73.487,4.162,73.568,4.246),[('马累',(73.505,4.175),-75,-23),('胡鲁马累',(73.5485,4.222),18,-20),('胡鲁累岛',(73.5288,4.198),-146,-17)])
]

def projection(bounds,width=1336,height=675):
    x0,y0,x1,y1=bounds
    cos=math.cos(math.radians((y0+y1)/2))
    m=min(width/((x1-x0)*cos),height/(y1-y0))
    def project(point):
        x,y=point[:2]
        return (width/2+(x-(x0+x1)/2)*m*cos,height/2- (y-(y0+y1)/2)*m)
    return project

def generate(index, view, world, local):
    n,cn,en,bounds,labels=view
    sw,sh=1464,647
    xy=projection(bounds,sw,sh)
    local_scale=index==2
    parts=[]
    def pth(coords,fill='none',stroke=PALETTE[2],weight=1.1,close=False):
        if len(coords)<2:return ''
        data=' '.join(f'{x:.2f},{y:.2f}' for x,y in map(xy,coords))
        tag='polygon' if close else 'polyline'
        return f'<{tag} points="{data}" fill="{fill}" stroke="{stroke}" stroke-width="{weight}" stroke-linejoin="round"/>'
    def label(x,y,value,size=22,fill=PALETTE[3],anchor='start'):
        return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}">{html.escape(value)}</text>'
    rings=local['coast'] if local_scale else world
    for ring in rings:
        if max(p[0] for p in ring)<bounds[0]-3 or min(p[0] for p in ring)>bounds[2]+3 or max(p[1] for p in ring)<bounds[1]-3 or min(p[1] for p in ring)>bounds[3]+3:
            continue
        parts.append(pth(ring,'#28518b',weight=1.5 if local_scale else 1,close=True))
    for group, color, weight, fill in [('runway','#c3dff6',4,'none'),('bridge','#9bbbdb',1.5,'none'),('terminal','#f2f7fc',2.4,'#6395c5')]:
        if local_scale:
            parts.extend(pth(a,fill,color,weight,group=='terminal') for a in local[group])
    for name,coord,dx,dy in labels:
        x,y=xy(coord)
        parts.append(label(x+dx,y+dy,name,27 if local_scale else 25,'#c3dbf1'))
    airport=AIRPORT
    if local_scale and local['terminal']:
        polygon=local['terminal'][0][:-1]
        airport=tuple(sum(p[k] for p in polygon)/len(polygon) for k in range(2))
    x,y=xy(airport)
    right=min(x+132,sw-270)
    ty=y+90 if local_scale else y-59
    parts.extend([f'<circle cx="{x:.1f}" cy="{y:.1f}" r="21" fill="none" stroke="#beddff" stroke-width="1.3"/>',
                  f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#eff8ff"/>',
                  f'<path d="M{x+7:.1f} {y:.1f}L{right-26:.1f} {ty:.1f}H{right+220:.1f}" fill="none" stroke="#c2dfff" stroke-width="1.5"/>',
                  label(right,ty-12,'维拉娜国际机场',27),label(right,ty+24,'MLE  /  VELANA INTERNATIONAL',15)])
    north='<path d="M1400 100v-47m-10 15 10-15 10 15" stroke="#d9ebfa" stroke-width="1.6" fill="none"/>'+label(1400,44,'N',16,anchor='middle')
    source='© OpenStreetMap contributors · ODbL' if local_scale else 'Natural Earth · 1:110m Land'
    scale=''
    if local_scale:
        x0,_=xy(AIRPORT); x1,_=xy((AIRPORT[0]+1/(111.32*math.cos(math.radians(AIRPORT[1]))), AIRPORT[1]))
        scale=f'<path d="M36 582v-10h{x1-x0:.1f}v10" fill="none" stroke="#d9ebfa" stroke-width="1.5"/>'+label(36,609,'1 km（约）',17)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
<defs><pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse"><path d="M0 48V0H48" fill="none" stroke="#9abcdf" stroke-opacity=".20" stroke-width="1"/></pattern>
<linearGradient id="sheet" x2=".8" y2="1"><stop stop-color="#102750"/><stop offset="1" stop-color="#214783"/></linearGradient><clipPath id="window"><rect width="{sw}" height="{sh}"/></clipPath></defs>
<style>text{{font-family:"Noto Sans CJK SC","Microsoft YaHei",sans-serif;letter-spacing:1px}}</style>
<rect width="{W}" height="{H}" fill="#0c1423"/>
<rect x="32" y="25" width="1536" height="850" fill="url(#sheet)"/>
<rect x="60" y="52" width="1480" height="796" fill="none" stroke="#8eafd6"/>
{label(75,87,'VELANA INTERNATIONAL AIRPORT  /  TERMINAL DEVELOPMENT',17)}
{label(74,135,cn,38)}{label(1525,135,'MAP '+n+'  /  '+en,21,anchor='end')}
<g transform="translate(68 151)" clip-path="url(#window)"><rect width="{sw}" height="{sh}" fill="url(#grid)"/>{''.join(parts)}{north}{scale}</g>
<path d="M67 800H1533" stroke="#87a7d2"/>
{label(75,829,'定位示意 · 北向上',17)}{label(1525,829,source,17,anchor='end')}
</svg>''', (round(x+68),round(y+151))

def animate(points):
    # Controlled camera move within each scale, matched on the airport marker.
    plates=[Image.open(ROOT/f'map-{i:02}.png').convert('RGB') for i in range(1,4)]
    out=ROOT/'Velana_Map_Zoom.mp4'
    with subprocess.Popen(['ffmpeg','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','24','-i','-','-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],stdin=subprocess.PIPE) as p:
        for i,(img,(px,py),length) in enumerate(zip(plates,points,[3,4,5])):
            # Keep the sheet header and attribution fixed while zooming the map inset.
            frame=img.resize((1280,720),Image.Resampling.LANCZOS)
            base=frame.crop((55,121,1225,638))
            x,y=px*.8-55,py*.8-121
            for n in range(length*24):
                t=n/(length*24)
                a=min(1,max(0,(t-.22)/.78))
                a=a*a*(3-2*a)
                scale=1+(0.25 if i<2 else .07)*a
                left=max(0,min(base.width-base.width/scale,x-x/scale))
                top=max(0,min(base.height-base.height/scale,y-y/scale))
                cam=base.transform(base.size,Image.Transform.EXTENT,(left,top,left+base.width/scale,top+base.height/scale),resample=Image.Resampling.BICUBIC)
                frame.paste(cam,(55,121))
                p.stdin.write(frame.tobytes())
        p.stdin.close()
        if p.wait():raise RuntimeError('FFmpeg render failed')

def main():
    natural=json.loads((ROOT/'world_land.geojson').read_text())
    world=[]
    for feature in natural['features']:
        geometry=feature['geometry']
        polygons=geometry['coordinates'] if geometry['type']=='MultiPolygon' else [geometry['coordinates']]
        world.extend(p[0] for p in polygons if p)
    local=json.loads((ROOT/'local_geometry.json').read_text())
    pts=[]
    for i,view in enumerate(VIEWS):
        drawing,point=generate(i,view,world,local)
        pts.append(point)
        svg=ROOT/f'map-{i+1:02}.svg'
        svg.write_text(drawing,encoding='utf-8')
        subprocess.run(['inkscape',str(svg),f'--export-filename={svg.with_suffix(".png")}',f'--export-width={W}'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    animate(pts)

if __name__=='__main__':
    main()
