#!/usr/bin/env python3
"""Regenerate Archit's themed animated banner and real-photo ASCII portrait.
Example (Windows PowerShell):
  python scripts/generate_profile_assets.py --photo "C:\\Users\\archi\\OneDrive\\Desktop\\yes1.jpg" --banner-art "C:\\Users\\archi\\Downloads\\pic.png"
The input images are read locally and are not copied into the repository.
"""
from pathlib import Path
import argparse
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance

ROOT=Path(__file__).resolve().parents[1]
DARK={'bg':'#080D18','bg2':'#0B1729','panel':'#0E1D32','panel2':'#12253D','border':'#263E5B','text':'#F3F7FF','muted':'#9DB2CB','dim':'#6C829D','blue':'#60A5FA','cyan':'#22D3EE','teal':'#2DD4BF','violet':'#A78BFA','amber':'#FBBF24','green':'#34D399','empty':'#172235','pill':'#122940'}
LIGHT={'bg':'#F5F8FC','bg2':'#E8F0FA','panel':'#FFFFFF','panel2':'#F2F7FD','border':'#CFDDED','text':'#132A45','muted':'#4E647E','dim':'#72869D','blue':'#2563EB','cyan':'#0891B2','teal':'#0F9F92','violet':'#7C3AED','amber':'#B45309','green':'#15803D','empty':'#E7EDF4','pill':'#E6F4FC'}
FONTS={
 'mono':[r'C:\Windows\Fonts\consola.ttf',r'C:\Windows\Fonts\lucon.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'],
 'monob':[r'C:\Windows\Fonts\consolab.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'],
 'sansb':[r'C:\Windows\Fonts\segoeuib.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'],
 'sans':[r'C:\Windows\Fonts\segoeui.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']}
def font(size,kind='sans'):
 for path in FONTS.get(kind,[]):
  try:return ImageFont.truetype(path,size)
  except Exception:pass
 return ImageFont.load_default()
def hx(s):
 s=s.lstrip('#');return tuple(int(s[i:i+2],16) for i in (0,2,4))
def rounded(d,box,r,fill,outline=None,width=1):d.rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=width)
def grad(im,a,b):
 d=ImageDraw.Draw(im);w,h=im.size;ca,cb=hx(a),hx(b)
 for x in range(w):
  t=x/max(1,w-1);col=tuple(round(ca[i]*(1-t)+cb[i]*t) for i in range(3));d.line((x,0,x,h),fill=col)
def save_gif(frames,path,duration=115,colors=128):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 pal=frames[len(frames)//2].convert('RGB').quantize(colors=colors,method=Image.Quantize.MEDIANCUT)
 q=[im.convert('RGB').quantize(palette=pal,dither=Image.Dither.NONE) for im in frames]
 q[0].save(path,save_all=True,append_images=q[1:],duration=duration,loop=0,optimize=True,disposal=2)
def matrix(path,cols,rows,transparent=False):
 im=Image.open(path).convert('RGBA')
 if not transparent:
  gray=ImageOps.autocontrast(ImageOps.grayscale(im),cutoff=1);gray=ImageEnhance.Contrast(gray).enhance(1.4);im=Image.merge('RGBA',(gray,gray,gray,im.getchannel('A')))
 im=im.resize((cols,rows),Image.Resampling.LANCZOS);pix=im.load();chars=' .,:-=+*#%@';out=[]
 for y in range(rows):
  row=[]
  for x in range(cols):
   r,g,b,a=pix[x,y];lum=.299*r+.587*g+.114*b
   if transparent and a<48:row.append((' ',lum,a));continue
   if not transparent and lum>248:row.append((' ',lum,a));continue
   idx=max(0,min(len(chars)-1,int((255-lum)/255*(len(chars)-1))))
   row.append((chars[idx],lum,a))
  out.append(row)
 return out
def art_color(lum,C,cartoon=False):
 if cartoon:
  if lum<80:return C['blue']
  if lum<145:return C['cyan']
  if lum<205:return C['teal']
  return C['text']
 if lum<60:return C['blue']
 if lum<105:return C['cyan']
 if lum<155:return C['teal']
 if lum<210:return C['muted']
 return C['text']
def draw_ascii(d,mat,x,y,cw,lh,fnt,rows,C,cartoon=False):
 for ri,row in enumerate(mat[:max(0,rows)]):
  for ci,(ch,lum,a) in enumerate(row):
   if ch!=' ':d.text((x+ci*cw,y+ri*lh),ch,font=fnt,fill=art_color(lum,C,cartoon))
def banner_frame(C,light,art,idx,total=56):
 W,H=850,440;im=Image.new('RGB',(W,H),C['bg']);grad(im,C['bg'],C['bg2']);d=ImageDraw.Draw(im)
 rounded(d,(1,1,W-2,H-2),20,C['bg'],C['border'],2);d.rectangle((1,1,W-2,35),fill=C['panel2']);d.line((1,35,W-2,35),fill=C['border'],width=1)
 for k,col in enumerate(['#FF6B6B','#FBBF24','#34D399']):d.ellipse((17+14*k,14,23+14*k,20),fill=col)
 d.text((60,10),'profile.sh --live ~',font=font(11,'mono'),fill=C['muted']);d.text((770,10),'PROFILE / 01',font=font(9,'monob'),fill=C['cyan'])
 rounded(d,(15,48,300,399),18,C['panel'],C['border'],2);rounded(d,(29,64,285,391),14,C['bg'],C['cyan'],2);rounded(d,(308,48,835,399),18,C['panel'],C['border'],2)
 rounded(d,(322,61,821,94),10,C['panel2'],C['border'],1);d.text((336,72),'SYSTEM.INFO',font=font(9,'monob'),fill=C['cyan']);rounded(d,(751,69,807,87),8,C['pill'],C['teal'],1);d.ellipse((760,75,766,81),fill=C['green']);d.text((772,73),'LIVE',font=font(8,'monob'),fill=C['teal'])
 d.rectangle((30,358,284,388),fill=C['bg']);d.text((42,366),'ASCII PORTRAIT',font=font(8,'monob'),fill=C['cyan']);d.text((42,378),'IMAGE -> MONOSPACE GLYPHS',font=font(7,'mono'),fill=C['dim']);d.text((43,406),'● PROFILE PIPELINE READY',font=font(8,'mono'),fill=C['teal']);d.text((322,375),'AGENTIC AI / NLP / RAG',font=font(8,'mono'),fill=C['muted']);d.text((756,375),'BUILD / 2026',font=font(8,'monob'),fill=C['amber'])
 n=len(art);reveal_end=18;hold_end=40;erase_end=53
 visible=round((idx+1)/reveal_end*n) if idx<reveal_end else n if idx<hold_end else round(max(0,(erase_end-idx)/(erase_end-hold_end)*n)) if idx<erase_end else 0
 cw,lh=5.2,8.3;aw=len(art[0])*cw;ah=n*lh;draw_ascii(d,art,42+(240-aw)/2,71+(278-ah)/2,cw,lh,font(8,'mono'),visible,C,True)
 rounded(d,(646,130,811,149),9,C['bg'],C['violet'],1);d.text((655,134),'@anshumanarchit-crypto',font=font(8,'mono'),fill=C['violet'])
 welcome='WELCOME';name="I'M ARCHIT ANSHUMAN"
 if idx<=10:title=welcome[:max(0,min(len(welcome),idx))];ts=34
 elif idx<=14:title=welcome;ts=34
 elif idx<=16:title=welcome[:max(0,len(welcome)-(idx-14)*4)];ts=34
 elif idx<=34:title=name[:round((idx-16)/18*len(name))];ts=25
 else:title=name;ts=25
 tf=font(ts,'sansb');d.text((334,99),title,font=tf,fill=C['cyan'] if not light else C['blue'])
 if idx in range(0,11) or idx in range(17,35):
  tx=334+d.textbbox((0,0),title,font=tf)[2]+3;d.rounded_rectangle((tx,103,tx+3,ts+106),radius=1,fill=C['amber'])
 if idx>=31:
  rows=[('ROLE','AI ENGINEERING INTERN'),('FOCUS','AGENTIC AI · NLP · RAG'),('EDUCATION','B.E. CSE · 2023—2027'),('CGPA','8.14 / 10'),('LOCATION','BENGALURU, INDIA')]
  y=159
  for lab,val in rows:d.text((334,y),lab,font=font(8,'mono'),fill=C['dim']);d.line((385,y+6,405,y+6),fill=C['border'],width=1);d.text((416,y-1),val,font=font(9,'monob'),fill=C['text']);y+=35
 base=428;xx=8+(idx%total)/total*825;d.line((7,base,843,base),fill=C['border'],width=1);d.line((8,base,xx,base),fill=C['blue'],width=2);d.line((max(8,xx-90),base,min(842,xx+35),base),fill=C['cyan'],width=2);d.ellipse((xx-4,base-4,xx+4,base+4),fill=C['cyan']);d.ellipse((xx-2,base-2,xx+2,base+2),fill=C['amber']);return im
def portrait_frame(C,light,mat,idx,total=81):
 W,H=840,880;im=Image.new('RGB',(W,H),C['bg']);grad(im,C['bg'],C['bg2']);d=ImageDraw.Draw(im);rounded(d,(5,5,W-5,H-5),18,C['panel'],C['border'],2);d.rectangle((6,6,W-6,42),fill=C['panel2']);d.line((6,42,W-6,42),fill=C['border'],width=1)
 for k,col in enumerate(['#FF6B6B','#FBBF24','#34D399']):d.ellipse((20+13*k,18,26+13*k,24),fill=col)
 d.text((W/2,18),'anshumanarchit-crypto@github:~$ ./portrait.sh',font=font(11,'mono'),fill=C['muted'],anchor='mt')
 nr=len(mat);visible=idx+1 if idx<58 else nr if idx<66 else max(0,nr-int((idx-65)/12*nr)) if idx<78 else 0
 cw,lh=10.5,11;aw=len(mat[0])*cw;ah=nr*lh;draw_ascii(d,mat,(W-aw)/2,70+(700-ah)/2,cw,lh,font(10,'mono'),visible,C,False)
 d.line((18,H-54,W-18,H-54),fill=C['border'],width=1);d.text((25,H-39),'ARCHIT ANSHUMAN',font=font(10,'monob'),fill=C['teal']);d.text((W-25,H-39),'REAL PHOTO / ASCII GLYPHS',font=font(9,'mono'),fill=C['muted'],anchor='rt');xx=30+(idx%32)*(W-60)/31;d.line((30,H-13,xx,H-13),fill=C['blue'],width=2);d.line((max(30,xx-70),H-13,min(W-30,xx+30),H-13),fill=C['cyan'],width=2);return im
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--photo',required=True);ap.add_argument('--banner-art',required=True);args=ap.parse_args();photo=Path(args.photo).expanduser();art=Path(args.banner_art).expanduser()
 if not photo.is_file():ap.error(f'Photo not found: {photo}')
 if not art.is_file():ap.error(f'Banner artwork not found: {art}')
 am=matrix(art,45,33,True);pm=matrix(photo,70,58,False)
 for C,suf,light in [(DARK,'dark',False),(LIGHT,'light',True)]:
  save_gif([banner_frame(C,light,am,i) for i in range(56)],ROOT/f'banner-{suf}.gif',120,128)
  save_gif([portrait_frame(C,light,pm,i) for i in range(81)],ROOT/'assets'/'animated'/f'profile-photo-ascii-{suf}.gif',85,112)
 print('Generated theme-aware banner and looping ASCII portrait GIFs. Source images were not copied.')
if __name__=='__main__':main()
