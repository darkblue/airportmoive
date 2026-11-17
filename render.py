import argparse
import os
from pathlib import Path
from functools import lru_cache
from math import sin,pi
from PIL import Image,ImageDraw,ImageFont,ImageOps
import subprocess,wave,struct

parser = argparse.ArgumentParser(description='Render the 75-second Velana trial cut.')
parser.add_argument('--materials', type=Path, required=True)
parser.add_argument('--bim', type=Path, required=True)
parser.add_argument('--output', type=Path, default=Path('output'))
parser.add_argument('--fonts', type=Path, default=Path(os.environ.get(
    'NOTO_CJK_DIR', '/usr/share/fonts/opentype/noto')))
args = parser.parse_args()
P, T = args.materials, args.output
(T / 'frames').mkdir(parents=True, exist_ok=True)
W,H,FPS=1280,720,25
DARK='#091e2e'; WHITE='#eaf4f7'; TEAL='#70e3c8'; MUTED='#99b7c5'; RED='#ff6966'; PANEL='#15364a'
@lru_cache(None)
def font(sz,b=False):
 return ImageFont.truetype(str(args.fonts / ('NotoSansCJK-' + ('Bold' if b else 'Regular') + '.ttc')),sz,index=2)
def tx(d,x,y,s,z,c=WHITE,b=False,anchor=None):
 d.text((x,y),s,font=font(z,b),fill=c,anchor=anchor)
def clamp(x):return max(0,min(1,x))
def ease(x):
 x=clamp(x);return x*x*(3-2*x)
def lerp(a,b,p):return a+(b-a)*p
def load(p):return Image.open(p).convert('RGB')
section=load(P/'02_Construction/Drawings/Velana_Cross_Section_05.png')
clash,resolved=[load(args.bim/(s+'.png')) for s in ['Clash','Resolved']]
lounge=load(P/'03_ELV_IT/T1_Lounge_Mihaaru.jpg')
pa=load(P/'03_ELV_IT/Velana_Broadcast_Coverage_2D.png')
def fit(im,w,h,cover=False):
 return (ImageOps.fit if cover else ImageOps.contain)(im,(w,h),method=Image.Resampling.BICUBIC)
def card(im,x,y,w,h,zoom=1,center=(.5,.5),cover=False):
 sw,sh=im.size
 if zoom!=1:
  cw,ch=sw/zoom,sh/zoom;cx,cy=center
  l=min(sw-cw,max(0,sw*cx-cw/2));t=min(sh-ch,max(0,sh*cy-ch/2))
  im=im.crop((round(l),round(t),round(l+cw),round(t+ch)))
 out=fit(im,w,h,cover)
 return (out,(x+(w-out.width)//2,y+(h-out.height)//2))
def pane(im,x,y,w,h,c,draw,**opts):
 draw.rounded_rectangle((x-1,y-1,x+w,y+h),radius=8,fill=c)
 loc=card(im,x,y,w,h,**opts)
 return loc
def imgpaste(bg,im,x,y,w,h,**opts):
 a,p=card(im,x,y,w,h,**opts);bg.paste(a,p)
def chrome(d,k,title,kicker,foot,info,progress):
 tx(d,44,18,'VELANA INTERNATIONAL AIRPORT  /  TERMINAL 1',15,TEAL,True)
 tx(d,42,43,title,34,WHITE,True)
 tx(d,1238,23,kicker,16,MUTED,True,anchor='ra')
 d.line((44,102,1238,102),fill='#2c4c60',width=1)
 d.rectangle((0,622,1280,720),fill='#0b2535')
 d.line((44,622,1238,622),fill='#285363',width=1)
 tx(d,44,640,foot,25,WHITE,True)
 tx(d,44,678,info,16,MUTED)
 tx(d,1238,682,f'{k:02d}  /  38',16,MUTED,True,anchor='ra')
 d.rectangle((0,716,int(W*progress),719),fill=TEAL)
def marker(d,x,y,p,label='CL-01'):
 pulse=2+int(3*(.5+.5*sin(p*4)))
 d.rounded_rectangle((x-57-pulse,y-43-pulse,x+58+pulse,y+44+pulse),radius=8,outline=RED,width=4)
 d.line((x+58,y-16,x+93,y-45,x+136,y-45),fill=RED,width=3)
 d.rounded_rectangle((x+127,y-62,x+209,y-29),radius=4,fill='#8f303a')
 tx(d,x+139,y-58,label,17,WHITE,True)
def main(t):
 bg=Image.new('RGB',(W,H),DARK);d=ImageDraw.Draw(bg)
 if t<10:
  p=ease((t-1)/8)
  d.rounded_rectangle((43,147,1238,536),radius=8,fill='#e4edf0')
  imgpaste(bg,section,54,162,1170,351,zoom=lerp(1,1.44,p),center=(.57,.51))
  if t>=3:
   a=ease((t-3)/1.7); d.rounded_rectangle((int(380+218*a),260,int(944-129*a),413),radius=7,outline='#118d84',width=3)
   d.rounded_rectangle((int(403+218*a),226,int(590+218*a),257),radius=4,fill='#114b57')
   tx(d,int(414+218*a),228,'值机大厅所在剖面',17,WHITE,True)
  chrome(d,12,'从总剖面定位吊顶管综','试剪 01  ·  01:10–01:45','从建筑总剖面进入吊顶机电节点。','图纸：Cross Section 05  ·  框选位置用于剪辑定位',t/35)
 elif t<23:
  u=t-10; z=lerp(1,1.13,ease(u/5))
  d.rounded_rectangle((45,120,1237,605),radius=8,fill='#adb5ba')
  imgpaste(bg,clash,45,120,1192,485,zoom=z)
  if u>=3.1:marker(d,640,369,u)
  chrome(d,13,'风管与桥架发生几何相交','试剪 01  ·  BIM 节点','蓝色风管与绿色弱电桥架在同一空间相交。','CL-01  ·  三维硬碰撞示意',t/35)
 else:
  u=t-23
  if u<5.2:
   for x,label,pic,c in [(44,'检查状态',clash,RED),(655,'标高调整后',resolved,TEAL)]:
    tx(d,x,127,label,22,c,True)
    imgpaste(bg,pic,x,166,580,385)
   marker(d,334,364,u)
  else:
   imgpaste(bg,resolved,45,116,1190,494,zoom=1.10)
   px,py=638,418
   d.ellipse((px-6,py-6,px+6,py+6),fill=TEAL)
   d.line((px,py,718,390,851,390),fill=TEAL,width=3)
   d.rounded_rectangle((847,369,1030,407),radius=4,fill='#12664f')
   tx(d,859,375,'桥架调整后标高',19,WHITE,True)
  chrome(d,14,'调整桥架标高，重新检查节点','试剪 01  ·  BIM 节点','调整后，桥架从风管下方通过。','同一视角比较检查状态与调整后状态  ·  影片示意',t/35)
 return bg
def panel(d,box,title,value,note,active=True):
 x,y,w,h=box
 d.rounded_rectangle((x,y,x+w,y+h),radius=14,fill=PANEL,outline='#315568',width=1)
 tx(d,x+22,y+16,title,23,TEAL if active else MUTED,True)
 tx(d,x+22,y+62,value,48,WHITE if active else '#829aa6',True)
 tx(d,x+22,y+h-35,note,16,MUTED)
def second(t):
 bg=Image.new('RGB',(W,H),DARK);d=ImageDraw.Draw(bg)
 if t<11:
  y=170
  if t<4:
   panel(d,(68,165,1144,374),'机场运行数据库  /  AODB','B04  →  B06','资源变更已确认  /  进入发布流程')
   tx(d,97,389,'模拟航班  VELANA DEMO 01',24,MUTED)
  elif t<7.4:
   panel(d,(68,165,1144,374),'航显  /  DEPARTURES','B06','演示航班  ·  登机口已更新')
   tx(d,97,389,'GATE CHANGE',24,TEAL,True)
  else:
   panel(d,(68,165,1144,374),'地服终端  /  GROUND HANDLING','B06','岗位收到登机口变更')
   tx(d,97,389,'RESOURCE UPDATE',24,TEAL,True)
  chrome(d,24,'AODB 发布，岗位与航显同步更新','试剪 02  ·  03:25–04:05','B06 从运行数据库传到航显和地服终端。','界面为虚构演示数据',t/40)
 elif t<23:
  u=t-11
  imgpaste(bg,lounge,44,119,1192,487,zoom=lerp(1,1.12,ease(u/10)),center=(.51,.49),cover=True)
  if u>3.2:
   d.rounded_rectangle((72,491,453,571),radius=9,fill='#0d3042')
   tx(d,92,499,'PA  /  广播提示',17,TEAL,True)
   tx(d,92,529,'登机口变更  ·  B06',24,WHITE,True)
  chrome(d,25,'进入候机区，广播接过提示','试剪 02  ·  候机区','广播按流程向候机区旅客发布变更提示。','实景照片：Fayaz Moosa / Mihaaru  ·  粗剪参考，成片需确认使用条件',t/40)
 else:
  u=t-23
  photo=fit(pa,1110,495)
  # Reveal the existing exact flat map, without remapping its coverage values.
  y0=112;x0=(W-photo.width)//2
  bg.paste(photo,(x0,y0))
  if u<1.35:
   p=ease(u/1.35)
   shade=Image.new('RGB',photo.size,DARK)
   bg.paste(Image.blend(shade,photo,p),(x0,y0))
  chrome(d,26,'扬声器布点与二维覆盖','试剪 02  ·  广播覆盖','两排扬声器下方及其间采用连续强覆盖示意。','覆盖色阶为画面示意  ·  不含现场测量值及 SPL / STI 仿真结果',t/40)
 return bg
target=T/'picture.mp4'
proc=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','-','-c:v','libx264','-preset','veryfast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(target)],stdin=subprocess.PIPE)
try:
 for frame in range(75*FPS):
  t=frame/FPS; im=main(t) if t<35 else second(t-35)
  if frame in [100,370,645,910,1250,1625]:im.save(T/'frames'/f'{frame:04d}.jpg',quality=91)
  proc.stdin.write(im.tobytes())
finally:
 proc.stdin.close()
if proc.wait() != 0:
 raise SystemExit('FFmpeg could not encode the picture track')
rate=24000
cues=[(2.1,450,.23),(10,190,.43),(13.3,680,.24),(23,330,.25),(35,510,.14),(39,850,.13),(42.4,740,.15),(48.9,660,.22),(49.13,880,.32),(58,340,.40)]
a=bytearray()
for i in range(75*rate):
 t=i/rate
 sample=(sin(2*pi*98*t)*.003+sin(2*pi*147*t)*.0025)*min(1,t/2,(75-t)/2)
 for start,hz,length in cues:
  k=t-start
  if 0<=k<length:sample+=.076*sin(2*pi*hz*k)*min(1,k/.014)*((1-k/length)**2)
 a+=struct.pack('<h',round(max(-1,min(1,sample))*32767))
with wave.open(str(T/'guide.wav'),'wb') as out:
 out.setparams((1,2,rate,0,'NONE','not compressed'));out.writeframes(a)

metadata = T / 'chapters.txt'
metadata.write_text(
    ';FFMETADATA1\n'
    '[CHAPTER]\nTIMEBASE=1/1000\nSTART=0\nEND=35000\ntitle=BIM协调\n'
    '[CHAPTER]\nTIMEBASE=1/1000\nSTART=35000\nEND=75000\ntitle=B06航显与广播\n',
    encoding='utf-8',
)
subprocess.run([
    'ffmpeg', '-v', 'error', '-y', '-i', str(target), '-i', str(T / 'guide.wav'),
    '-i', str(metadata), '-map', '0:v:0', '-map', '1:a:0',
    '-map_metadata', '2', '-map_chapters', '2', '-c:v', 'copy',
    '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart',
    str(T / 'Velana_Film_Trial_Cut.mp4'),
], check=True)
