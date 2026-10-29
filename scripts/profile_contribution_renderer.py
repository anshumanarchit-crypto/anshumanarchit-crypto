#!/usr/bin/env python3
"""Shared contribution GIF renderer used by scheduled workflow. All cards consume the same JSON snapshot."""
from pathlib import Path
import json, math, datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT=Path(__file__).resolve().parents[1]
DARK={'bg':'#080D18','bg2':'#0B1729','panel':'#0E1D32','panel2':'#12253D','border':'#263E5B','text':'#F3F7FF','muted':'#9DB2CB','dim':'#6C829D','blue':'#60A5FA','cyan':'#22D3EE','teal':'#2DD4BF','violet':'#A78BFA','amber':'#FBBF24','green':'#34D399','grid':'#1D2A3D','empty':'#172235'}
LIGHT={'bg':'#F5F8FC','bg2':'#E8F0FA','panel':'#FFFFFF','panel2':'#F2F7FD','border':'#CFDDED','text':'#132A45','muted':'#4E647E','dim':'#72869D','blue':'#2563EB','cyan':'#0891B2','teal':'#0F9F92','violet':'#7C3AED','amber':'#B45309','green':'#15803D','grid':'#DAE5F1','empty':'#E7EDF4'}
FONTS={'mono':'/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf','monob':'/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf','sans':'/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','sansb':'/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'}
def f(sz,k='sans'):
    try:return ImageFont.truetype(FONTS[k],sz)
    except:return ImageFont.load_default()
def rgb(s):
    s=s.lstrip('#');return tuple(int(s[i:i+2],16) for i in (0,2,4))
def rounded(d,b,r,fill,outline=None,width=1):d.rounded_rectangle(b,radius=r,fill=fill,outline=outline,width=width)
def draw_bg(sz,C):
    im=Image.new('RGB',sz,C['bg']); d=ImageDraw.Draw(im); a,b=rgb(C['bg']),rgb(C['bg2']); w,h=sz
    for x in range(w):
        t=x/max(1,w-1); c=tuple(round(a[i]*(1-t)+b[i]*t) for i in range(3)); d.line((x,0,x,h),fill=c)
    return im
def save(frames,path,duration=105,colors=128):
    pal=frames[len(frames)//2].convert('RGB').quantize(colors=colors,method=Image.Quantize.MEDIANCUT)
    q=[im.convert('RGB').quantize(palette=pal,dither=Image.Dither.NONE) for im in frames]
    Path(path).parent.mkdir(parents=True,exist_ok=True);q[0].save(path,save_all=True,append_images=q[1:],duration=duration,loop=0,optimize=True,disposal=2)
def draw_overview(C,data,idx,n=32):
    W,H=1120,300; im=draw_bg((W,H),C); d=ImageDraw.Draw(im); rounded(d,(2,2,W-2,H-2),18,C['panel'],C['border'],2); d.rectangle((3,3,W-3,43),fill=C['panel2']);d.line((3,43,W-3,43),fill=C['border'],width=1);d.ellipse((20,18,28,26),fill=C['teal']);d.text((W/2,14),'PROFILE TELEMETRY / ONE CONTRIBUTION SNAPSHOT',font=f(11,'monob'),fill=C['muted'],anchor='mt')
    vals=[('TOTAL CONTRIBUTIONS',data['total_contributions'],C['blue']),('ACTIVE DAYS',data['active_days'],C['teal']),('CURRENT STREAK',data['current_streak']['length'],C['amber'])]; cw=(W-44-32)//3
    for i,(lab,val,col) in enumerate(vals):
        x=22+i*(cw+16);rounded(d,(x,62,x+cw,173),12,C['panel2'],C['border'],1);d.text((x+18,79),lab,font=f(11,'monob'),fill=C['muted']);v=round(val*min(1,(idx+1)/12));d.text((x+18,108),str(v),font=f(34,'sansb'),fill=col);d.text((x+18,149),['in the last year','contribution days','days'][i],font=f(11,'mono'),fill=C['dim'])
    d.text((24,207),f"LONGEST STREAK  {data['longest_streak']['length']} DAYS",font=f(12,'monob'),fill=C['muted']);d.text((W-24,207),f"BEST DAY  {data['best_day']['count']}",font=f(12,'monob'),fill=C['amber'],anchor='rt');y=255;d.line((24,y,W-24,y),fill=C['border'],width=2);x=24+(idx%(n-1))/(n-1)*(W-48);d.line((24,y,x,y),fill=C['blue'],width=2);d.line((max(24,x-120),y,min(W-24,x+20),y),fill=C['cyan'],width=3);d.ellipse((x-4,y-4,x+4,y+4),fill=C['cyan']);d.text((24,274),f"DATA SOURCE  github.com/users/{data.get('username','anshumanarchit-crypto')}/contributions",font=f(9,'mono'),fill=C['dim']);return im
def draw_activity(C,data,idx,n=40):
    W,H=1120,340;im=Image.new('RGB',(W,H),C['bg']);d=ImageDraw.Draw(im);rounded(d,(2,2,W-2,H-2),18,C['panel'],C['border'],2);d.rectangle((3,3,W-3,40),fill=C['panel2']);d.line((3,40,W-3,40),fill=C['border'],width=1)
    for k,col in enumerate(['#FF6B6B','#FBBF24','#34D399']):d.ellipse((20+13*k,17,27+13*k,24),fill=col)
    d.text((W/2,14),'GITHUB ACTIVITY / LAST 31 DAYS',font=f(11,'monob'),fill=C['muted'],anchor='mt');days=data['days'][-31:];vals=[x['count'] for x in days];mv=max(vals+[1]);left,right,top,bot=65,W-36,82,267
    for j in range(5):
        y=top+j*(bot-top)/4;d.line((left,y,right,y),fill=C['grid'],width=1);d.text((26,y-6),str(round(mv*(4-j)/4)),font=f(9,'mono'),fill=C['dim'])
    pts=[(left+i*(right-left)/max(1,len(vals)-1),bot-v/mv*(bot-top)) for i,v in enumerate(vals)];prog=min(len(pts),max(2,round((idx+1)/n*len(pts))))
    for x,y in pts:d.ellipse((x-1.5,bot-1.5,x+1.5,bot+1.5),fill=C['dim'])
    if len(pts)>1:d.line(pts,fill=C['border'],width=2);d.line(pts[:prog],fill=C['blue'],width=3);x,y=pts[prog-1];d.ellipse((x-6,y-6,x+6,y+6),fill=C['cyan']);d.ellipse((x-2,y-2,x+2,y+2),fill=C['text'])
    if days:d.text((left,290),datetime.date.fromisoformat(days[0]['date']).strftime('%b %d'),font=f(9,'mono'),fill=C['muted']);d.text((right,290),datetime.date.fromisoformat(days[-1]['date']).strftime('%b %d'),font=f(9,'mono'),fill=C['muted'],anchor='rt')
    d.text((W-30,50),f'{sum(vals)} contributions',font=f(10,'monob'),fill=C['teal'],anchor='rt');return im
def draw_heatmap(C,data,idx,n=42):
    W,H=1120,340;im=Image.new('RGB',(W,H),C['bg']);d=ImageDraw.Draw(im);rounded(d,(2,2,W-2,H-2),18,C['panel'],C['border'],2);d.rectangle((3,3,W-3,40),fill=C['panel2']);d.line((3,40,W-3,40),fill=C['border'],width=1);d.ellipse((19,17,27,25),fill=C['teal']);d.text((W/2,14),'ANNUAL CONTRIBUTION HEATMAP',font=f(12,'sansb'),fill=C['text'],anchor='mt');d.text((W/2,51),f"{data.get('username','anshumanarchit-crypto')} / contribution field",font=f(9,'mono'),fill=C['muted'],anchor='mt')
    days=data['days'];grid=[];first=datetime.date.fromisoformat(days[0]['date']);col=[None]*first.weekday()
    for it in days:
        wd=datetime.date.fromisoformat(it['date']).weekday()
        while len(col)<wd:col.append(None)
        col.append(it)
        if len(col)==7:grid.append(col);col=[]
    if col:
        while len(col)<7:col.append(None)
        grid.append(col)
    cell,gap,step,left,top=14,4,19,48,92;seen=set()
    for ci,week in enumerate(grid):
        for it in week:
            if it:
                dt=datetime.date.fromisoformat(it['date']);key=(dt.year,dt.month)
                if key not in seen and dt.day<=7:seen.add(key);d.text((left+ci*step,70),dt.strftime('%b'),font=f(10,'mono'),fill=C['muted'])
                break
    pal=[C['empty'],'#123A35' if C is DARK else '#D7F4EF','#0F766E' if C is DARK else '#99E6DC','#14B8A6' if C is DARK else '#2CB9AA',C['teal'],C['cyan']];progress=max(0,min(1,idx/(n-1)));total=len(grid)*7
    for ri,daylabel in enumerate(['S','M','T','W','T','F','S']):
        d.text((23,top+ri*step+3),daylabel,font=f(9,'mono'),fill=C['dim'])
    for ci,week in enumerate(grid):
        for ri,it in enumerate(week):
            if not it:continue
            count=it['count'];lvl=0 if count==0 else 1 if count<=2 else 2 if count<=5 else 3 if count<=10 else 4 if count<=20 else 5;visible=ci*7+ri<=int(progress*total);color=pal[lvl] if visible else C['panel2'];x=left+ci*step;y=top+ri*step;rounded(d,(x,y,x+cell,y+cell),3,color)
    d.line((20,257,W-20,257),fill=C['border'],width=1);d.text((24,275),f"{data['total_contributions']:,} contributions in the last year",font=f(12,'sansb'),fill=C['text']);d.text((W/2,275),f"{data['active_days']} active days",font=f(11,'mono'),fill=C['teal'],anchor='mt');d.text((W-24,275),f"CURRENT {data['current_streak']['length']}D  ·  LONGEST {data['longest_streak']['length']}D",font=f(10,'mono'),fill=C['muted'],anchor='rt');d.text((24,310),'LESS',font=f(8,'mono'),fill=C['dim'])
    for i,c in enumerate(pal):rounded(d,(62+i*16,303,73+i*16,314),2,c)
    d.text((168,309),'MORE',font=f(8,'mono'),fill=C['dim']);xx=24+(idx%n)/(n-1)*(W-48);d.line((24,331,xx,331),fill=C['blue'],width=2);d.line((max(24,xx-55),331,min(W-24,xx+20),331),fill=C['cyan'],width=2);d.ellipse((xx-3,328,xx+3,334),fill=C['amber']);return im
def draw_stats(C,data,idx,n=40):
    W,H=840,880;im=Image.new('RGB',(W,H),C['bg']);d=ImageDraw.Draw(im);rounded(d,(4,4,W-4,H-4),18,C['panel'],C['border'],2);d.rectangle((5,5,W-5,43),fill=C['panel2']);d.line((5,43,W-5,43),fill=C['border'],width=1)
    for k,col in enumerate(['#FF6B6B','#FBBF24','#34D399']):d.ellipse((21+13*k,18,28+13*k,25),fill=col)
    d.text((W/2,14),'anshumanarchit-crypto@github:~$ ./stats.sh',font=f(10,'mono'),fill=C['muted'],anchor='mt');labs=[('current streak',data['current_streak']['length'],'days',C['green']),('longest streak',data['longest_streak']['length'],'days',C['blue']),('contributions',data['total_contributions'],'in the last year',C['text']),('active days',data['active_days'],f"/ {len(data['days'])} days",C['teal']),('best day',data['best_day']['count'],data['best_day']['date'],C['amber']),('avg / active day',data['avg_per_active_day'],'contributions',C['violet'])]
    for i,(label,val,suffix,col) in enumerate(labs):
        x=20+(i%2)*401;y=62+(i//2)*132;rounded(d,(x,y,x+385,y+118),12,C['panel2'],C['border'],1);d.text((x+16,y+13),'$ '+label,font=f(11,'mono'),fill=C['muted']);reveal=min(1,(idx+1)/12);number=round(val*reveal) if idx<11 and i<4 else (f'{val:.1f}' if isinstance(val,float) else str(val));d.text((x+16,y+42),str(number),font=f(28,'monob'),fill=col);d.text((x+16,y+83),suffix,font=f(10,'mono'),fill=C['dim'])
    monthly=data['monthly'][-12:];y0=486;rounded(d,(20,y0,820,815),14,C['bg2'],C['border'],1);d.text((40,y0+18),'$ contributions / month',font=f(12,'mono'),fill=C['muted']);pt,pb,pl,pr=y0+75,770,43,800;slot=(pr-pl)/max(1,len(monthly));peak=max([m['total'] for m in monthly]+[1])
    for i,m in enumerate(monthly):
        bh=max(3,(pb-pt)*m['total']/peak);x=pl+i*slot+slot*.2;bw=slot*.56;hh=bh*min(1,max(.03,(idx+1)/max(1,n-1)*1.15));rounded(d,(x,pb-hh,x+bw,pb),4,C['green'] if m['total']==peak and m['total'] else C['teal']);d.text((x+bw/2,pb+14),datetime.date.fromisoformat(m['month']+'-01').strftime('%b')[0],font=f(8,'mono'),fill=C['dim'],anchor='mt')
    d.text((40,790),f"ONE SNAPSHOT · {data['total_contributions']} CONTRIBUTIONS · {data['active_days']} ACTIVE DAYS",font=f(9,'mono'),fill=C['teal']);return im
def draw_snake(C,data,idx,n=40):
    W,H=1120,210;im=Image.new('RGB',(W,H),C['bg']);d=ImageDraw.Draw(im);rounded(d,(2,2,W-2,H-2),16,C['panel'],C['border'],2);days=data['days'];grid=[];first=datetime.date.fromisoformat(days[0]['date']);col=[None]*first.weekday()
    for it in days:
        wd=datetime.date.fromisoformat(it['date']).weekday()
        while len(col)<wd:col.append(None)
        col.append(it)
        if len(col)==7:grid.append(col);col=[]
    if col:
        while len(col)<7:col.append(None)
        grid.append(col)
    cell,gap,step,left,top=12,5,17,34,25;head=int((idx/(n-1))*max(1,len(grid)*7));trail=15
    for ci,week in enumerate(grid):
        for ri,it in enumerate(week):
            if not it:continue
            lvl=0 if it['count']==0 else 1 if it['count']<=2 else 2 if it['count']<=5 else 3 if it['count']<=15 else 4;pal=[C['empty'],'#12453F' if C is DARK else '#CBF2EB','#117C70' if C is DARK else '#85DBD0','#20B9AA',C['teal']];color=pal[lvl];order=ci*7+ri
            if head-trail<=order<=head:color=C['cyan'] if order==head else C['teal']
            rounded(d,(left+ci*step,top+ri*step,left+ci*step+cell,top+ri*step+cell),3,color)
    y=160;d.line((28,y,W-28,y),fill=C['border'],width=1);d.text((30,174),f"anshumanarchit-crypto · {data['total_contributions']} contributions · looping contribution snake",font=f(10,'mono'),fill=C['muted']);pos=28+idx/(n-1)*(W-56);d.line((28,154,pos,154),fill=C['blue'],width=2);d.line((max(28,pos-60),154,min(W-28,pos+20),154),fill=C['teal'],width=2);return im
def gen_contribution_assets_from_file(root,data):
    for C,suf in [(DARK,'dark'),(LIGHT,'light')]:
        save([draw_overview(C,data,i) for i in range(32)],root/'assets/animated'/f'developer-overview-{suf}.gif',110,112)
        save([draw_activity(C,data,i) for i in range(40)],root/'assets/animated'/f'activity-graph-{suf}.gif',100,112)
        save([draw_heatmap(C,data,i) for i in range(42)],root/'assets/animated'/f'annual-heatmap-{suf}.gif',105,128)
        save([draw_stats(C,data,i) for i in range(40)],root/'assets/animated'/f'contribution-stats-{suf}.gif',105,128)
        save([draw_snake(C,data,i) for i in range(40)],root/'assets/animated'/f'contribution-snake-{suf}.gif',105,112)
if __name__=='__main__':
    data=json.loads((ROOT/'data'/'contributions.json').read_text(encoding='utf-8'));gen_contribution_assets_from_file(ROOT,data);print(f"Refreshed contribution assets from {data['total_contributions']} contributions.")
