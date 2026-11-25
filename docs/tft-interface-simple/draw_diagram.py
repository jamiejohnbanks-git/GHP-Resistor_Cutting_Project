from pathlib import Path
import html,json
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUT=Path(__file__).resolve().parent
OUT.mkdir(parents=True,exist_ok=True)
pdfmetrics.registerFont(TTFont('Sans','/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Bold','/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'))
W,H=420,297
c=canvas.Canvas(str(OUT/'Nano-TFT-SN74LVC245A.pdf'),pagesize=(W*mm,H*mm))
c.setTitle('Nano to TFT - SN74LVC245A - software SPI')
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297"><rect width="420" height="297" fill="white"/>']
INK='#173145';BLUE='#166b90';RED='#ad2935';GREEN='#126d53'
nets={};segments=[]
def txt(x,y,s,size=3,col=INK,bold=False):
 c.setFillColor(col);c.setFont('Bold' if bold else 'Sans',size*mm);c.drawString(x*mm,(H-y)*mm,s)
 svg.append(f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{col}">{html.escape(s)}</text>')
def line(x,y,xx,yy,col=BLUE,net=None):
 c.setStrokeColor(col);c.setLineWidth(.4*mm);c.line(x*mm,(H-y)*mm,xx*mm,(H-yy)*mm)
 svg.append(f'<line x1="{x}" y1="{y}" x2="{xx}" y2="{yy}" stroke="{col}" stroke-width=".4"/>')
 if net:segments.append(dict(net=net,a=[x,y],b=[xx,yy]))
def box(x,y,w,h,col=INK):
 c.setStrokeColor(col);c.setLineWidth(.3*mm);c.rect(x*mm,(H-y-h)*mm,w*mm,h*mm)
 svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{col}" stroke-width=".3"/>')
def dot(x,y):
 c.setFillColor(BLUE);c.circle(x*mm,(H-y)*mm,.75*mm,fill=1,stroke=0)
 svg.append(f'<circle cx="{x}" cy="{y}" r=".75" fill="{BLUE}"/>')
def net(name,*pins):nets[name]=list(pins)

txt(12,15,'NANO TO TFT - SN74LVC245A',6,bold=True)
txt(12,23,'Software SPI | DIP20 pin numbers | No resistor voltage dividers | Signal diagram, not a motor or regulator schematic',3)
box(12,29,396,11,RED)
txt(16,36,'Keep motor wiring unchanged. TFT VCC / LED power and installed chip identities still require the checks below.',3.1,RED,True)
box(12,46,76,130);box(135,46,110,130);box(307,46,101,130)
txt(17,54,'NANO / MR PCB',3.6,bold=True)
txt(142,54,'U1  SN74LVC245A',3.7,bold=True)
txt(142,60,'5V-tolerant A inputs -> 3.3V B outputs',2.65)
txt(313,54,'ILI9341 TFT + TOUCH',3.3,bold=True)
chs=[('D13','Nano pin',2,18,['SCK','T_CLK'],'CLOCK'),('D3','ENCODER pin 5',3,17,['SDI / MOSI','T_DIN'],'MOSI'),('A4','I2C pin 3',4,16,['CS'],'LCD_CS'),('A5','I2C pin 4',5,15,['D/C'],'DC'),('D4','ENCODER pin 3',6,14,['T_CS'],'TOUCH_CS'),('RESET','Nano RESET pin',7,13,['RESET'],'RESET')]
for i,(pin,access,a,b,dest,name) in enumerate(chs):
 y=68+20*i
 txt(18,y,pin,3.6,bold=True);txt(18,y+5,access,2.65)
 line(88,y,135,y,net=name+'_5V');txt(140,y+1,f'{a}  A{i+1}',3.3,bold=True)
 txt(176,y+1,'--->',3,BLUE)
 txt(217,y+1,f'B{i+1}  {b}',3.3,bold=True)
 if len(dest)==2:
  line(245,y,286,y,net=name+'_3V3');dot(286,y)
  line(286,y-3,286,y+3,net=name+'_3V3')
  for off,p in zip([-3,3],dest):
   line(286,y+off,307,y+off,net=name+'_3V3');txt(313,y+off+1,p,3.15,bold=True)
 else:
  line(245,y,307,y,net=name+'_3V3');txt(313,y+1,dest[0],3.3,bold=True)
 net(name+'_5V','NANO.'+pin,f'U1.{a}')
 net(name+'_3V3',f'U1.{b}',*['TFT.'+p for p in dest])
 if name in ['LCD_CS','TOUCH_CS']:
  r='R1' if name=='LCD_CS' else 'R2'
  dot(110,y);line(110,y,110,y-6,net=name+'_5V');box(108.5,y-12,3,6)
  line(110,y-12,110,y-15,GREEN,'5V');txt(114,y-9,r+' 10k',2.5);txt(114,y-15,'Nano 5V',2.4,GREEN)
  nets[name+'_5V'].append(r+'.2')

# Reverse direction is shown separately, not through U1.
txt(12,185,'TOUCH DATA RETURNS TO NANO THROUGH A SEPARATE 5V BUFFER',3.1,bold=True)
box(135,190,110,20);txt(143,197,'U2  SN74AHCT125 (DIP14)',3.1,bold=True)
txt(140,205,'3  1Y   <---   1A  2',3.2,bold=True)
line(88,203,135,203,net='TOUCH_5V');txt(18,204,'D2 / ENCODER pin 4',3.1,bold=True)
line(245,203,307,203,net='TOUCH_3V3');txt(313,204,'T_OUT',3.3,bold=True)
net('TOUCH_3V3','TFT.T_OUT','U2.2');net('TOUCH_5V','U2.3','NANO.D2')

box(12,217,193,52);box(213,217,195,52)
txt(17,224,'U1 POWER AND CONTROL - DO NOT APPLY 5V TO PIN 20',3,RED,True)
for j,s in enumerate(['Pin 20 (VCC) -> regulated 3.3V; pin 1 (DIR) -> 3.3V.',
 'Pins 10 (GND) and 19 (/OE) -> common GND.',
 'C1: 100nF directly between pins 20 and 10.',
 'Unused inputs 8, 9 -> GND; outputs 11, 12 unconnected.',
 'R1/R2 above hold both CS inputs HIGH during Nano reset.',
 'Logical symbol, NOT physical package view: locate pin 1 by notch/dot.']):txt(17,231+6*j,s,2.7)
txt(218,224,'U2 POWER / UNUSED CHANNELS AND TFT POWER',3,bold=True)
for j,s in enumerate(['Pin 14 -> Nano 5V; pins 7 (GND), 1 (/OE) -> GND.',
 'C2: 100nF directly between pins 14 and 7.',
 'Unused /OE 4,10,13 -> 5V; inputs 5,9,12 -> GND;',
 'unused outputs 6,8,11 unconnected. Do not substitute HC125.',
 'TFT GND -> common GND. VCC: regulated 5V, verify U1/J1 on TFT.',
 'LED: leave open until current limiting/supply confirmed.']):txt(218,231+6*j,s,2.7)

net('3V3','REGULATOR.3V3','U1.20','U1.1','C1.1')
net('5V','NANO.5V','U2.14','U2.4','U2.10','U2.13','C2.1','R1.1','R2.1')
net('GND','NANO.GND','TFT.GND','REGULATOR.GND','U1.10','U1.19','U1.8','U1.9','C1.2','U2.7','U2.1','U2.5','U2.9','U2.12','C2.2')
net('TFT_VCC_CONDITIONAL','REGULATED_5V.OUT','TFT.VCC')
txt(12,277,'Leave TFT SDO/MISO, T_IRQ and SD-card pins open. Encoder/I2C devices unplugged. Power together; verify reset sequencing.',2.85)
txt(12,283,'3.3V source: complete AP63203QWU-7 circuit or regulated module. Keep D5/D6, A0-A3 and D7-D12 on their existing motor functions.',2.65)
txt(12,291,'RRC-TFT-002 Rev A | 26 Nov 2026 | New software-SPI map: replaces earlier hardware-SPI proposal | Confirm actual IC package markings.',2.65,RED,True)

seen={}
for n,pins in nets.items():
 for p in pins:
  assert p not in seen,(p,n,seen.get(p));seen[p]=n
assert len(chs)==6 and all(seen[f'U1.{a}']==name+'_5V' and seen[f'U1.{b}']==name+'_3V3' for _,_,a,b,_,name in chs)
assert seen['U1.20']=='3V3' and seen['U1.19']=='GND'
assert not any('NANO.'+p in seen for p in ['D5','D6','D7','D8','D9','D10','D11','D12','A0','A1','A2','A3'])
def cross(a,b):
 ax,ay=a['a'];bx,by=a['b'];cx,cy=b['a'];dx,dy=b['b']
 if ax==bx and cx==dx:return ax==cx and max(min(ay,by),min(cy,dy))<=min(max(ay,by),max(cy,dy))
 if ay==by and cy==dy:return ay==cy and max(min(ax,bx),min(cx,dx))<=min(max(ax,bx),max(cx,dx))
 if ay==by:return cross(b,a)
 return min(cx,dx)<=ax<=max(cx,dx) and min(ay,by)<=cy<=max(ay,by)
for i,a in enumerate(segments):
 for b in segments[i+1:]:assert a['net']==b['net'] or not cross(a,b),(a,b)
svg.append('</svg>');(OUT/'Nano-TFT-SN74LVC245A.svg').write_text('\n'.join(svg))
c.save();(OUT/'connections.json').write_text(json.dumps({'nets':nets,'drawn_segments':segments,'checks':'unique net membership, six channels, motor pins preserved, no different-net crossings','conditions':['TFT VCC regulator/jumper and LED connection','Actual LCD and touch controller identities/return VOH','Power sequencing and reset behavior']},indent=2))
print('Generated PDF/SVG/netlist; pin and crossing checks passed.')
