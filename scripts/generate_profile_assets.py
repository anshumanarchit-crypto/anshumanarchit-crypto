#!/usr/bin/env python3
"""Generate theme-aware SVG charts/cards from the repository's real contribution JSON.
Uses only Python's standard library. Writes XML-validated SVGs to the repository root/assets.
"""
from pathlib import Path
import datetime, json, html, xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "contributions.json"
PALETTES = {
 "dark": {"bg":"#0B1220","panel":"#101B2D","panel2":"#13233A","line":"#243956","text":"#F1F6FF","muted":"#9CB0CA","blue":"#5B8CFF","teal":"#51D9C4","amber":"#FFB86B","coral":"#FF8C7A","green":"#7CE6B4","grid":"#213650","cells":["#172235","#144B46","#147D70","#25A695","#51D9C4"]},
 "light": {"bg":"#F3F7FC","panel":"#FFFFFF","panel2":"#EAF1F9","line":"#D5E1EF","text":"#172941","muted":"#60748D","blue":"#285DCE","teal":"#087F78","amber":"#AD5A1A","coral":"#BC5548","green":"#147D55","grid":"#DCE6F2","cells":["#E6EDF5","#C4E9E2","#81D8C7","#3ABAA8","#087F78"]}
}
def e(v): return html.escape(str(v), quote=True)
def txt(x,y,value,size,color,weight=400,anchor="start",mono=False):
    ff='font-family="Cascadia Code,Consolas,monospace"' if mono else 'font-family="Inter,Segoe UI,Arial,sans-serif"'
    return f'<text x="{x}" y="{y}" {ff} font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{e(value)}</text>'
def save(path,w,h,body,p):
    css="""text{font-family:Inter,"Segoe UI",Arial,sans-serif}.mono{font-family:"Cascadia Code",Consolas,monospace}.cell{opacity:0;animation:cell .38s ease-out forwards}.bar{transform-box:fill-box;transform-origin:bottom;animation:grow .7s ease-out both}.trace{stroke-dasharray:10 12;animation:trace 16s linear infinite}@keyframes cell{to{opacity:1}}@keyframes grow{from{transform:scaleY(.12);opacity:.35}to{transform:scaleY(1);opacity:1}}@keyframes trace{to{stroke-dashoffset:-500}}"""
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><title>{e(path.stem.replace("-"," "))}</title><style>{css}</style>{body}</svg>'
    ET.fromstring(svg)
    path.write_text(svg,encoding='utf-8')
def load():
    if DATA.exists():
        try:
            d=json.loads(DATA.read_text(encoding='utf-8'))
            return d
        except Exception as ex: print('Warning: unable to read contribution data:',ex)
    # Honest non-numeric placeholder when no daily source data is present.
    return {"username":"anshumanarchit-crypto","generated_at":"","total_contributions":0,"active_days":0,"current_streak":{"length":0},"longest_streak":{"length":0},"best_day":{"count":0},"monthly":[],"days":[]}
def level(n): return 0 if n<=0 else 1 if n<=1 else 2 if n<=3 else 3 if n<=5 else 4

def heatmap(d,theme):
    p=PALETTES[theme]; days=d.get('days',[])
    w,h=1200,254
    b=[f'<rect width="{w}" height="{h}" rx="17" fill="{p["panel"]}" stroke="{p["line"]}"/>',f'<rect x="0" y="0" width="1200" height="36" rx="17" fill="{p["panel2"]}"/>',f'<rect x="0" y="24" width="1200" height="12" fill="{p["panel2"]}"/>']
    for i,c in enumerate(['#FF6B6B','#FFCA6A',p['teal']]): b.append(f'<circle cx="19" cy="18" r="4.5" fill="{c}"/>')
    b.append(txt(600,22,'anshumanarchit-crypto  /  contribution field',11,p['muted'],600,'middle',True))
    if not days:
        b.append(txt(600,118,'Contribution data not found',21,p['text'],700,'middle'))
        b.append(txt(600,147,'Run fetch_contributions.py, then generate_profile_assets.py',12,p['muted'],500,'middle',True))
        save(ROOT/('contrib-heatmap.svg' if theme=='dark' else 'contrib-heatmap-light.svg'),w,h,''.join(b),p); return
    # Use Sunday-first columns to match a GitHub contribution calendar.
    parsed=[]
    for item in days:
        dt=datetime.date.fromisoformat(item['date']); parsed.append((dt,int(item.get('count',0))))
    first=parsed[0][0]; start=first-datetime.timedelta(days=(first.weekday()+1)%7)
    last=parsed[-1][0]; weeks=((last-start).days+7)//7
    cell=13; gap=4; x0=48; y0=68
    months=[]; prior=None
    daymap={dt:cnt for dt,cnt in parsed}
    for wi in range(weeks):
        date=start+datetime.timedelta(days=wi*7)
        if date.month!=prior:
            months.append((wi,date.strftime('%b'))); prior=date.month
    for wi,m in months:
        b.append(txt(x0+wi*(cell+gap),57,m,10,p['muted'],500))
    for row,day in enumerate(['S','M','T','W','T','F','S']): b.append(txt(22,y0+row*(cell+gap)+10,day,9,p['muted'],500,'middle',True))
    for wi in range(weeks):
        for r in range(7):
            dt=start+datetime.timedelta(days=wi*7+r)
            if dt not in daymap: continue
            cnt=daymap[dt]; lv=level(cnt); x=x0+wi*(cell+gap); y=y0+r*(cell+gap)
            b.append(f'<rect class="cell" style="animation-delay:{wi*0.012+r*0.018:.3f}s" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{p["cells"][lv]}"><title>{e(dt.isoformat())}: {cnt} contributions</title></rect>')
    # footer and honest totals from source
    total=d.get('total_contributions',sum(x['count'] for x in days)); active=d.get('active_days',sum(1 for x in days if x['count']>0))
    b.append(f'<line x1="18" y1="202" x2="1182" y2="202" stroke="{p["line"]}"/>')
    b.append(txt(24,225,f'{total} contributions in the last year',13,p['text'],700,mono=True))
    b.append(txt(465,225,f'{active} active days',12,p['teal'],600,mono=True))
    b.append(txt(900,225,'LESS',9,p['muted'],500,'end',True))
    for i,c in enumerate(p['cells']): b.append(f'<rect x="{914+i*17}" y="213" width="13" height="13" rx="3" fill="{c}"/>')
    b.append(txt(1005,225,'MORE',9,p['muted'],500,'start',True))
    save(ROOT/('contrib-heatmap.svg' if theme=='dark' else 'contrib-heatmap-light.svg'),w,h,''.join(b),p)

def stats(d,theme):
    p=PALETTES[theme]; monthly=d.get('monthly',[])[-12:]; total=int(d.get('total_contributions',0)); active=int(d.get('active_days',0)); current=int((d.get('current_streak') or {}).get('length',0)); longest=int((d.get('longest_streak') or {}).get('length',0)); best=int((d.get('best_day') or {}).get('count',0))
    w,h=600,390
    b=[f'<rect width="600" height="390" rx="18" fill="{p["panel"]}" stroke="{p["line"]}"/>',f'<rect x="0" y="0" width="600" height="38" rx="18" fill="{p["panel2"]}"/>',f'<rect x="0" y="25" width="600" height="13" fill="{p["panel2"]}"/>']
    for i,c in enumerate(['#FF6B6B','#FFCA6A',p['teal']]): b.append(f'<circle cx="20" cy="19" r="4.5" fill="{c}"/>')
    b.append(txt(300,23,'PROFILE TELEMETRY  /  12-MONTH WINDOW',10,p['muted'],650,'middle',True))
    cards=[('CONTRIBUTIONS',str(total),p['blue']),('ACTIVE DAYS',str(active),p['teal']),('CURRENT STREAK',f'{current}d',p['amber'])]
    for i,(k,v,c) in enumerate(cards):
        x=18+i*190
        b.append(f'<rect x="{x}" y="53" width="174" height="77" rx="12" fill="{p["panel2"]}" stroke="{p["line"]}"/>')
        b.append(txt(x+13,76,k,9,p['muted'],650,mono=True))
        b.append(txt(x+13,111,v,27,c,750))
    b.append(txt(22,162,'MONTHLY CONTRIBUTION PULSE',10,p['muted'],700,mono=True))
    plotx,ploty,plotw,ploth=32,184,536,116
    vals=[int(x.get('total',0)) for x in monthly] or [0]*12; maxv=max(vals) if max(vals)>0 else 1
    bw=25; g=18
    for i,v in enumerate(vals[-12:]):
        hh=max(3,(v/maxv)*80); x=plotx+i*(bw+g); y=ploty+85-hh
        b.append(f'<rect class="bar" style="animation-delay:{i*0.055:.2f}s" x="{x}" y="{y:.1f}" width="{bw}" height="{hh:.1f}" rx="5" fill="{p["teal"]}" fill-opacity="{0.6+0.4*(v/maxv):.2f}"/>')
        if monthly and i<len(monthly):
            month=datetime.datetime.strptime(monthly[i].get('month','2000-01'),'%Y-%m').strftime('%b')
        else: month=''
        b.append(txt(x+bw/2,ploty+103,month,8,p['muted'],500,'middle',True))
    b.append(f'<line x1="24" y1="317" x2="576" y2="317" stroke="{p["line"]}"/>')
    b.append(txt(24,340,f'LONGEST STREAK  {longest} DAYS',10,p['muted'],650,mono=True))
    b.append(txt(575,340,f'BEST DAY  {best}',10,p['amber'],700,'end',True))
    b.append(txt(24,370,'Data: GitHub public contribution calendar',9,p['muted'],500,mono=True))
    b.append(txt(575,370,'AUTO-SYNC',9,p['teal'],700,'end',True))
    save(ROOT/('stats.svg' if theme=='dark' else 'stats-light.svg'),w,h,''.join(b),p)

def activity(d,theme):
    p=PALETTES[theme]; monthly=d.get('monthly',[])[-12:]; vals=[int(x.get('total',0)) for x in monthly]; labels=[datetime.datetime.strptime(x.get('month','2000-01'),'%Y-%m').strftime('%b') for x in monthly]
    w,h=1200,240
    b=[f'<rect width="1200" height="240" rx="16" fill="{p["panel"]}" stroke="{p["line"]}"/>',txt(24,30,'CONTRIBUTION SIGNAL  /  MONTHLY',11,p['muted'],700,mono=True)]
    if vals:
        maxv=max(vals) or 1; points=[]
        for i,v in enumerate(vals):
            x=46+i*(1108/max(1,len(vals)-1)); y=166-(v/maxv)*105; points.append((x,y))
        path=' '.join(f'{x:.1f},{y:.1f}' for x,y in points)
        b.append(f'<polyline points="{path}" fill="none" stroke="{p["teal"]}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1400" stroke-dashoffset="1400"><animate attributeName="stroke-dashoffset" from="1400" to="0" dur="2.2s" fill="freeze"/></polyline>')
        for i,((x,y),v) in enumerate(zip(points,vals)):
            b.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{p["blue"]}" class="pulse"><title>{v} contributions</title></circle>')
            b.append(txt(x,199,labels[i] if i<len(labels) else '',9,p['muted'],500,'middle',True))
    else:
        b.append(txt(600,126,'Run the contribution fetcher to populate this graph',14,p['muted'],500,'middle',True))
    b.append(f'<path d="M24 211 H1176" stroke="{p["line"]}"/>')
    b.append(txt(24,229,'MONTHLY ACTIVITY',9,p['muted'],650,mono=True)); b.append(txt(1176,229,'ANSUMANARCHIT-CRYPTO',9,p['teal'],700,'end',True))
    save(ROOT/'assets'/'animated'/f'activity-graph-{theme}.svg',w,h,''.join(b),p)

def main():
    d=load()
    # write dynamic visuals and keep the user-supplied portrait/banner artwork intact
    for t in ('dark','light'):
        heatmap(d,t); stats(d,t); activity(d,t)
    print('Generated and XML-validated: contrib-heatmap.svg, contrib-heatmap-light.svg, stats.svg, stats-light.svg, activity graph variants.')
if __name__=='__main__': main()
