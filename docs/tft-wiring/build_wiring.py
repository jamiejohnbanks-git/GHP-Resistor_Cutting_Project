from pathlib import Path
import json, csv, html, math, shutil
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont('WiringSans','/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'))
pdfmetrics.registerFont(TTFont('WiringBold','/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'))

# Run from the project root; outputs are written to ./output.
OUT = Path('output')
OUT.mkdir(exist_ok=True)
W,H=420,297
INK='#182b3a'; BLUE='#16698b'; RED='#b12935'; GREY='#566673'; GREEN='#14735b'
CHANNELS=[
 dict(pin='D10',name='LCD_CS',dest=['CS'],y=64,conflict='L298N input 3',header='Nano D10'),
 dict(pin='D7',name='LCD_RST',dest=['RESET'],y=87,conflict='L298N input 1',header='Nano D7'),
 dict(pin='D8',name='LCD_DC',dest=['D/C'],y=110,conflict='L298N input 2',header='Nano D8'),
 dict(pin='D11',name='SPI_MOSI',dest=['SDI (MOSI)','T_DIN'],y=133,conflict='L298N input 4',header='Nano D11'),
 dict(pin='D13',name='SPI_SCK',dest=['SCK','T_CLK'],y=156,conflict=None,header='Nano D13'),
 dict(pin='D4',name='TOUCH_CS',dest=['T_CS'],y=179,conflict='Encoder header if occupied',header='ENCODER pin 3'),
]
NETS={}
COMPONENTS=[]
def net(name,*ends):
    NETS.setdefault(name,[]).extend(ends)
for i,ch in enumerate(CHANNELS):
    a,b=f'R{2*i+1}',f'R{2*i+2}'
    ch['upper']=a;ch['lower']=b
    COMPONENTS += [dict(ref=a,value_ohms=1000,tolerance_percent=1),dict(ref=b,value_ohms=2000,tolerance_percent=1)]
    net(ch['name']+'_5V','NANO.'+ch['pin'],a+'.1')
    net(ch['name']+'_3V3',a+'.2',b+'.1',*['TFT.'+p for p in ch['dest']])
    net('GND',b+'.2')
net('SPI_MISO','NANO.D12','JP3.1','JP4.1')
net('LCD_SDO','JP3.2','TFT.SDO (MISO)')
net('TOUCH_DO','JP4.2','TFT.T_OUT')
net('TOUCH_IRQ_OPTIONAL','NANO.D2','JP5.1')
net('TOUCH_IRQ','JP5.2','TFT.T_IRQ')
net('12V','SUPPLY.+','PCB.12V_IN','BUCK.VIN+')
net('GND','SUPPLY.-','PCB.GND','NANO.GND','BUCK.VIN-','BUCK.VOUT-','TFT.GND','C1.2','C2.2')
net('3V3','BUCK.VOUT+','JP1.1','JP2.1')
net('TFT_VCC','JP1.2','TFT.VCC','C1.1','C2.1')
net('BACKLIGHT_SUPPLY','JP2.2','TFT.LED')
COMPONENTS += [dict(ref=f'JP{i}',type='normally-open commissioning link') for i in range(1,6)]
COMPONENTS += [dict(ref='C1',value='100nF ceramic, >=10V'),dict(ref='C2',value='10uF, >=10V; polarity as marked'),dict(ref='BUCK',value='Complete 12V-input / 3.3V-output module, >=500mA continuous')]
DOC=dict(title='Nano / KMRTM24024-SPI conditional hardware-SPI interface',revision='B',status='NOT RELEASED FOR WIRING OR POWER-UP',netlist=NETS,components=COMPONENTS,channels=CHANNELS,links={
 'JP1':'Close only after validating module VCC and 3.3V regulator bypass arrangement',
 'JP2':'Close only after validating backlight voltage and current limiting',
 'JP3':'Display SDO: close only if tri-state and return voltage margins verified',
 'JP4':'Touch T_OUT: close only if tri-state and return voltage margins verified',
 'JP5':'Optional interrupt: close only after voltage and pull-up verification'},
 unresolved=['Actual LCD / touch controller identity','D7/D8/D10/D11 isolation from L298N','D12 EN-link state and isolation from both A4988 enable inputs','TFT VCC regulator/jumper configuration','Backlight current limiting','Divider recommended operating voltage compliance','AVR input-high margin on 3.3V return signals','Shared MISO high-impedance behavior'])
(OUT/'connection-netlist.json').write_text(json.dumps(DOC,indent=2))
with (OUT/'connections.csv').open('w',newline='') as f:
    wr=csv.writer(f);wr.writerow(['Net','Endpoints'])
    for k,v in NETS.items():wr.writerow([k,' ; '.join(v)])

class Drawing:
    def __init__(self,pdf):self.c=pdf;self.svg=[];self.wires=[];self.page=0
    def begin(self):
        self.page+=1;self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297"><rect width="420" height="297" fill="white"/>'];self.wires=[]
    def line(self,x1,y1,x2,y2,color=INK,width=.35,dash=False,netname=None):
        c=self.c;c.setStrokeColor(color);c.setLineWidth(width*mm);c.setDash([2*mm,1.3*mm] if dash else [])
        c.line(x1*mm,(H-y1)*mm,x2*mm,(H-y2)*mm)
        ds=' stroke-dasharray="2 1.3"' if dash else ''
        self.svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{ds}/>')
        if netname:self.wires.append(dict(page=self.page,net=netname,a=[x1,y1],b=[x2,y2]))
    def wire(self,x1,y1,x2,y2,n,color=BLUE,dash=False):self.line(x1,y1,x2,y2,color,.38,dash,n)
    def rect(self,x,y,w,h,color=INK,fill=None):
        c=self.c;c.setStrokeColor(color);c.setLineWidth(.3*mm);c.setFillColor(fill or '#ffffff');c.rect(x*mm,(H-y-h)*mm,w*mm,h*mm,stroke=1,fill=1)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill or "white"}" stroke="{color}" stroke-width=".3"/>')
    def text(self,x,y,s,size=2.7,color=INK,bold=False):
        font='WiringBold' if bold else 'WiringSans';self.c.setFont(font,size*mm);self.c.setFillColor(color);self.c.drawString(x*mm,(H-y)*mm,s)
        self.svg.append(f'<text x="{x}" y="{y}" font-family="Helvetica,Arial,sans-serif" font-size="{size}" font-weight="{"bold" if bold else "normal"}" fill="{color}">{html.escape(s)}</text>')
        assert 0 <= x and x+stringWidth(s,font,size*mm)/mm < 419,(s,x)
    def dot(self,x,y):
        self.c.setFillColor(BLUE);self.c.circle(x*mm,(H-y)*mm,.8*mm,fill=1,stroke=0)
        self.svg.append(f'<circle cx="{x}" cy="{y}" r=".8" fill="{BLUE}"/>')
    def ground(self,x,y):
        for dy,w in [(0,4),(1.2,2.7),(2.4,1.2)]:self.line(x-w/2,y+dy,x+w/2,y+dy,GREY,.3)
        self.text(x+4,y+1.4,'GND',2.2,GREY)
    def link(self,x,y,label):
        self.line(x,y,x+5,y-2,RED,.45)
        self.text(x-1,y-3.5,label,2.2,RED)
        # Actual drawing is an open link, with no conductor across gap.
    def footer(self,sheet):
        self.line(10,284,410,284,GREY)
        self.text(12,290,'RRC-TFT-001 | Rev B | 20 Nov 2026 | A3 landscape | NOT RELEASED',2.5,RED,True)
        self.text(316,290,f'{sheet} | Dots = junctions; same net names connect',2.3,GREY)
    def end(self,name):
        self.svg.append('</svg>');(OUT/name).write_text('\n'.join(self.svg));all_wires.extend(self.wires);self.c.showPage()

pdf=canvas.Canvas(str(OUT/'Nano-TFT-wiring-A3.pdf'),pagesize=(W*mm,H*mm))
pdf.setTitle('Resistor Reel Cutter - Nano TFT Wiring - Conditional Design Rev B')
all_wires=[];d=Drawing(pdf)
d.begin()
d.text(12,15,'ARDUINO NANO + SPI TOUCHSCREEN',6,INK,True)
d.text(12,23,'Explicit netlist schematic | Proposed hardware-SPI assignment from the supplied brief',3,GREY)
d.rect(12,29,396,12,RED,'#fff2f0')
d.text(16,36.7,'HOLD: isolate occupied PCB nets and resolve electrical checks on Sheet 2 before connecting.',3.5,RED,True)
d.rect(12,48,68,190)
d.text(17,55,'NANO ON MR PCB',3.5,INK,True)
d.rect(284,48,124,190)
d.text(290,55,'KMRTM24024-SPI',3.5,INK,True)
for ch in CHANNELS:
    y=ch['y'];nhi=ch['name']+'_5V';nlo=ch['name']+'_3V3'
    d.text(18,y,ch['pin'],3.6,INK,True)
    d.text(18,y+5,ch['header'],2.3,GREY)
    d.text(18,y+10,'ISOLATE: '+ch['conflict'] if ch['pin'] in ['D7','D8','D10','D11'] else ('Encoder must be unused' if ch['pin']=='D4' else 'No load shown on PCB'),2.15,RED if ch['conflict'] else GREY)
    d.wire(80,y,104,y,nhi)
    d.rect(104,y-1.5,12,3)
    d.text(102,y-4,f"{ch['upper']}  1k",2.6)
    d.wire(116,y,139,y,nlo)
    d.dot(139,y)
    d.wire(139,y,139,y+6,nlo)
    d.rect(137.5,y+6,3,6)
    d.text(144,y+10,f"{ch['lower']}  2k",2.5)
    d.wire(139,y+12,139,y+16,'GND',GREY)
    d.ground(139,y+16)
    d.text(161,y-4,ch['name']+'_3V3',2.5,BLUE)
    if len(ch['dest'])==1:
        d.wire(139,y,284,y,nlo)
        d.text(290,y+1,ch['dest'][0],3.2,INK,True)
    else:
        d.wire(139,y,259,y,nlo)
        d.dot(259,y)
        d.wire(259,y-3,259,y+3,nlo)
        for off,pin in zip([-3,3],ch['dest']):
            d.wire(259,y+off,284,y+off,nlo)
            d.text(290,y+off+1,pin,3.1,INK,True)
    if ch['pin'] in ['D7','D8','D10','D11']:
        d.text(334,y+10,'PCB NET CONFLICT',2.25,RED,True)

y=211
d.text(18,y,'D12 / MISO',3.5,INK,True)
d.text(18,y+5,'EN link: verify / isolate',2.3,RED)
d.text(18,y+10,'Input only after isolation',2.3,GREY)
d.wire(80,y,230,y,'SPI_MISO');d.dot(230,y)
d.wire(230,y-4,230,y+4,'SPI_MISO')
for yy,jp,pin,n in [(207,'JP3','SDO (MISO)','LCD_SDO'),(215,'JP4','T_OUT (= T_DO)','TOUCH_DO')]:
    d.wire(230,yy,253,yy,'SPI_MISO');d.link(253,yy,jp)
    d.wire(260,yy,284,yy,n)
    d.text(290,yy+1,pin,3,INK,True)
d.text(163,223,'JP3/JP4 OPEN until bus-release + input margins verified',2.5,RED)
y=232
d.text(18,y,'D2 / IRQ optional',3,INK,True)
d.wire(80,y,253,y,'TOUCH_IRQ_OPTIONAL',BLUE,True);d.link(253,y,'JP5')
d.wire(260,y,284,y,'TOUCH_IRQ',BLUE,True);d.text(290,y+1,'T_IRQ (optional)',3)
d.text(90,244,'JP3-JP5 are commissioning links; drawn OPEN. No hidden direct connection across an open link.',2.6,RED)
d.rect(12,250,396,27,GREY,'#f3f7f9')
d.text(17,257,'POWER AND EXISTING MOTORS',3,INK,True)
d.text(17,264,'See Sheet 2 for 12V split, regulated 3.3V, common ground, VCC/backlight conditions and parts list.',2.8)
d.text(17,271,'Keep MG90S on D5/D6 and A4988 STEP/DIR on A0-A3. SD-card pins unused. Do not load older D12-enable firmware.',2.6)
d.footer('Sheet 1/2');d.end('signal-schematic-A3.svg')

d.begin();d.text(12,15,'POWER, PARTS & RELEASE CHECKS',6,INK,True)
d.text(12,23,'Read with Sheet 1 | Wiring is conditional; no actual controller identity or module power configuration is assumed',2.9,GREY)
# Power tree. No wire crossings: branches to existing PCB and module.
d.rect(12,33,52,22);d.text(17,42,'12V DC SUPPLY',3.4,INK,True);d.text(17,49,'Existing machine supply',2.6)
d.wire(64,40,89,40,'12V',RED);d.dot(89,40)
d.wire(89,40,89,63,'12V',RED);d.wire(89,63,111,63,'12V',RED)
d.rect(111,54,65,22);d.text(116,63,'MR INNOVATIVE PCB',3,INK,True);d.text(116,70,'Existing 12V input',2.5)
d.wire(89,40,198,40,'12V',RED)
d.rect(198,32,78,25);d.text(203,40,'COMPLETE BUCK MODULE',3,INK,True)
d.text(203,46,'12V in / 3.3V out',2.8);d.text(203,52,'>=500mA continuous; verify load',2.5)
d.wire(276,40,290,40,'3V3',GREEN);d.dot(290,40)
d.wire(290,40,314,40,'3V3',GREEN);d.link(314,40,'JP1')
d.wire(321,40,343,40,'TFT_VCC',GREEN);d.text(347,41,'TFT VCC',3,INK,True)
d.wire(290,40,290,64,'3V3',GREEN);d.wire(290,64,314,64,'3V3',GREEN);d.link(314,64,'JP2')
d.wire(321,64,343,64,'BACKLIGHT_SUPPLY',GREEN);d.text(347,65,'TFT LED',3,INK,True)
d.text(296,49,'JP1: VCC verified first',2.4,RED)
d.text(296,73,'JP2: backlight verified first',2.4,RED)
d.text(12,84,'GND: supply negative + PCB/Nano ground + buck VIN-/VOUT- + TFT GND + every divider lower end.',2.8,INK,True)
d.text(12,95,'PCB 5V is the Nano rail; +5V is the servo rail. Verify paralleled 7805 outputs and STEP pull-downs marked 200 ohms.',2.6,RED)
d.text(12,90,'C1 100nF and C2 10uF connect across TFT VCC/GND near the header. Do not join 3.3V to Nano 5V or servo power.',2.6)
# Two report columns, avoiding cross-column text.
def lines(x,y,items,size=2.65,leading=4.5,color=INK):
    for s in items:d.text(x,y,s,size,color);y+=leading
    return y
d.text(12,102,'A. PCB PIN CONFLICTS',3.5,RED,True)
lines(12,109,[
 'D7/D8/D10/D11 already feed the L298N inputs.',
 'Hardware SPI will toggle the L298N unless these nets are isolated.',
 'D12 reaches BOTH A4988 enables through the 2-pin EN link.',
 'With EN link fitted, MISO conflicts with the motor enables.',
 'Remove/verify EN link before MISO; keep driver enables defined.',
 'D9 controls BOTH L298N enables; LOW disables those bridges.',
 'Motor unplugging alone does not isolate these logic connections.',
 'Removing power from an IC alone can cause signal back-powering.',
 'D4/D2: leave encoder unplugged. D0/D1: preserve USB Serial.',
 'D5/D6: keep cutter servos. A0-A3: keep step/dir connections.',
 'This hardware-SPI map is NOT approved on an unmodified PCB.'
],2.55,4.3)
d.text(218,102,'B. DIVIDER VOLTAGE CHECK',3.5,INK,True)
lines(218,109,[
 'Rupper=1k; Rlower=2k. Nominal: 5.00 x 2/3 = 3.333V.',
 'Assumed high=5.25V, resistors +/-1%: worst case 3.523V.',
 'At +/-5% resistance tolerance: worst case 3.615V.',
 'ILI9341 example: recommended input HIGH <= VDDI;',
 'absolute maximum is VDDI+0.3V. Absolute max is not a target.',
 'At VDDI=3.30V, even nominal 3.333V exceeds the stated',
 'recommended ceiling. At lower VDDI, margin is smaller.',
 'Therefore 1k/2k dividers are shown as requested, NOT approved',
 'for a guaranteed-compliant interface. Verify actual IC specs.',
 'Recommended: SN74LVC245A at TFT logic 3.3V; 5.5V-tolerant',
 'inputs; DIR=HIGH for A->B, /OE=LOW; 100nF decoupling.'
],2.55,4.3)
d.text(12,165,'C. POWER AND RETURN SIGNALS',3.5,INK,True)
lines(12,172,[
 'Read U1 marking and inspect J1 on the actual TFT before power-up.',
 '3.3V at VCC may require bypassing its onboard regulator.',
 'Do not bridge J1 by guesswork. Measure the actual logic rail.',
 'LED needs confirmed current limiting / a suitable driver.',
 'Do not drive the backlight from a Nano GPIO.',
 'Direct 3.3V MISO/IRQ to 5V AVR is conditional: verify VOH >=',
 'AVR VIH (typically 0.6 x VCC for these pins). A 3.3V rail alone',
 'does not guarantee VOH. Use a 5V AHCT input buffer if needed.',
 'Verify both chips release MISO when deselected before JP3+JP4.',
 'If not, leave display SDO open and use touch-only readback.',
 'Identify actual LCD / touch IC before selecting software libraries.'
],2.55,4.3)
d.text(218,165,'D. PARTS FOR THE CONDITIONAL DIVIDER DESIGN',3.5,INK,True)
lines(218,172,[
 '6 x 1k ohm, 1%, >=0.125W (R1/R3/R5/R7/R9/R11).',
 '6 x 2k ohm, 1%, >=0.125W (R2/R4/R6/R8/R10/R12).',
 '1 x complete regulated 3.3V buck module, >=500mA continuous,',
 '     rated for 12V input; size for measured display+backlight load.',
 '1 x 100nF ceramic + 1 x 10uF capacitor, >=10V, near TFT.',
 '5 x optional commissioning links, breadboard, short jumpers,',
 '     multimeter; scope / logic analyser for SPI integrity checks.',
 'AP63203QWU-7 is a regulator IC, NOT a ready-to-wire module.',
 'For a custom buck PCB, follow the current Diodes reference',
 'design: inductor, input/output/bootstrap capacitors, FB/EN',
 'connections and switching-loop layout. Do not breadboard it.'
],2.55,4.3)
d.rect(12,225,396,29,RED,'#fff2f0')
lines(16,232,[
 'RELEASE CHECKS: photograph/identify ICs and jumpers; confirm PCB isolation by continuity; resolve level shifting both directions;',
 'verify VCC/backlight arrangement; verify shared-MISO release; check 3.3V polarity/voltage under load before closing JP1/JP2.',
 'First display test: isolate actuators; start SPI slowly and inspect waveforms. Then integrate with the working cutter firmware.'
],2.65,7,RED)
lines(12,262,[
 'Sources: original MR Innovative multipurpose schematic (Rev 1.0, 2021-01-22); ILI9341 manufacturer datasheet Sections 18.1/18.2;',
 'TI SN74LVC245A product/datasheet; Diodes AP63203Q product and AP63203QWU-EVM guide. Full URLs in handoff-notes.md; corrections in wiring-review.md.'
],2.5,5,GREY)
d.footer('Sheet 2/2');d.end('power-and-checks-A3.svg');pdf.save()

# Validate the electrical specification and the actual rendered wire geometry.
seen={}
for n,ends in NETS.items():
    assert len(ends)==len(set(ends)), ('duplicate endpoint',n)
    for ep in ends:
        assert ep not in seen,('endpoint on two nets',ep)
        seen[ep]=n
assert len(CHANNELS)==6
assert NETS['SPI_SCK_3V3']==['R9.2','R10.1','TFT.SCK','TFT.T_CLK']
assert NETS['SPI_MOSI_3V3']==['R7.2','R8.1','TFT.SDI (MOSI)','TFT.T_DIN']
assert seen['NANO.D12']=='SPI_MISO' and seen['NANO.D2']=='TOUCH_IRQ_OPTIONAL'
assert 'NANO.D5' not in seen and 'NANO.D6' not in seen
assert seen['NANO.D4']=='TOUCH_CS_5V'
def intersects(a,b):
    ax,ay=a['a'];bx,by=a['b'];cx,cy=b['a'];dx,dy=b['b']
    if ax==bx and cx==dx:return ax==cx and max(min(ay,by),min(cy,dy))<=min(max(ay,by),max(cy,dy))
    if ay==by and cy==dy:return ay==cy and max(min(ax,bx),min(cx,dx))<=min(max(ax,bx),max(cx,dx))
    if ay==by:a,b=b,a;ax,ay=a['a'];bx,by=a['b'];cx,cy=b['a'];dx,dy=b['b']
    return min(cx,dx)<=ax<=max(cx,dx) and min(ay,by)<=cy<=max(ay,by)
bad=[]
for i,a in enumerate(all_wires):
    assert a['a'][0]==a['b'][0] or a['a'][1]==a['b'][1]
    for b in all_wires[i+1:]:
        if a['page']==b['page'] and a['net']!=b['net'] and intersects(a,b):bad.append([a,b])
assert not bad,bad
max1=5.25*2020/(990+2020);max5=5.25*2100/(950+2100)
report={'checks_passed':['Every electrical endpoint belongs to exactly one named net','Six independently defined upper/lower divider pairs','Shared SCK and MOSI branches use one divider each','D4 is touch CS, D13 is clock, D12 is MISO, D2 is optional IRQ','Servo signals D5/D6 are excluded','No different-net wire crossings or overlaps in rendered drawings','Every rendered conductor is recorded with net name and endpoints','Text stays within A3 horizontal bounds'], 'electrical_release':'BLOCKED: see unresolved conditions; geometry checks do not approve hardware','divider_worst_case_V':{'nominal_5V':5*2/3,'5.25V_1pct':max1,'5.25V_5pct':max5},'rendered_wire_segments':len(all_wires)}
(OUT/'validation-report.json').write_text(json.dumps(report,indent=2))
(OUT/'rendered-wire-segments.json').write_text(json.dumps(all_wires,indent=2))
shutil.copy(__file__,OUT/'build_wiring.py')
print(json.dumps(report,indent=2))
