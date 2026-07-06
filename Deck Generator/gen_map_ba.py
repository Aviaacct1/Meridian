import math
DARK=(31,56,100); CYAN=(0,176,240); ORANGE=(237,125,49); LAND=(224,230,238); OCEAN=(247,249,251); MUT=(90,105,125)
W,H=1500,820
LON0,LON1,LAT0,LAT1=-128,10,30,66
def proj(lat,lon): return (lon-LON0)/(LON1-LON0)*W,(LAT1-lat)/(LAT1-LAT0)*H
def gc(lat1,lon1,lat2,lon2,n=90):
    la1,lo1,la2,lo2=map(math.radians,[lat1,lon1,lat2,lon2])
    d=2*math.asin(math.sqrt(math.sin((la2-la1)/2)**2+math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2));P=[]
    for i in range(n+1):
        f=i/n;A=math.sin((1-f)*d)/math.sin(d);B=math.sin(f*d)/math.sin(d)
        x=A*math.cos(la1)*math.cos(lo1)+B*math.cos(la2)*math.cos(lo2);y=A*math.cos(la1)*math.sin(lo1)+B*math.cos(la2)*math.sin(lo2);z=A*math.sin(la1)+B*math.sin(la2)
        P.append((math.degrees(math.atan2(z,math.sqrt(x*x+y*y))),math.degrees(math.atan2(y,x))))
    return P
from PIL import Image,ImageDraw,ImageFont
img=Image.new("RGB",(W,H),OCEAN);d=ImageDraw.Draw(img)
for lon in range(-120,11,15):
    x,_=proj(0,lon);d.line([(x,0),(x,H)],fill=(236,240,244),width=1)
for lat in range(30,67,10):
    _,y=proj(lat,0);d.line([(0,y),(W,y)],fill=(236,240,244),width=1)
polys=[
 [(-128,49),(-123,34),(-112,31),(-95,30),(-82,31),(-70,45),(-74,52),(-95,60),(-120,60),(-128,55)],
 [(-52,66),(-30,66),(-22,61),(-44,60)],
 [(-10,59),(8,59),(8,43),(-2,43),(-6,50),(-10,54)],
 [(-10,38),(8,38),(8,30),(-10,30)],
]
for poly in polys: d.polygon([proj(la,lo) for lo,la in poly],fill=LAND,outline=(196,205,216))
P=[proj(la,lo) for la,lo in gc(51.47,-0.46,37.36,-121.93)]
for i in range(0,len(P)-1,2): d.line([P[i],P[i+1]],fill=ORANGE,width=5)
def fnt(sz,b=True):
    try: return ImageFont.truetype("DejaVuSans-Bold.ttf" if b else "DejaVuSans.ttf",sz)
    except: return ImageFont.load_default()
def mark(lat,lon,name,side):
    x,y=proj(lat,lon);d.ellipse([x-10,y-10,x+10,y+10],fill=DARK);d.ellipse([x-5,y-5,x+5,y+5],fill=ORANGE)
    f=fnt(30);tw=d.textlength(name,font=f)
    d.text((x-tw-16 if side=="l" else x+16,y-16),name,fill=DARK,font=f)
mark(51.47,-0.46,"London","l");mark(37.36,-121.93,"San Jose","r")
mid=P[len(P)//2];d.text((mid[0]-90,mid[1]-44),"circa 4,620 nm",fill=MUT,font=fnt(26,False))
img.save("route_map_ba.png");print("ok",img.size)
