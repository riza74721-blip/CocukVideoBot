import asyncio, json, math, random, subprocess
from datetime import date
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts

ROOT=Path(__file__).parent
OUT=ROOT/"output"
OUT.mkdir(exist_ok=True)
stories=json.loads((ROOT/"stories.json").read_text(encoding="utf-8"))
story=stories[date.today().toordinal()%len(stories)]
fontfile="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
font=ImageFont.truetype(fontfile,76)
small=ImageFont.truetype(fontfile,40)
colors=[(248,91,103),(76,153,247),(253,203,68),(85,198,133),(170,105,228),(252,158,72)]
random.seed(date.today().isoformat())

def frame(i,step):
    im=Image.new("RGB",(720,1280),(243,249,255))
    d=ImageDraw.Draw(im)
    # sky and rolling hills
    d.ellipse((-150,900,850,1590),fill=(155,223,172))
    d.ellipse((-250,1080,460,1540),fill=(116,203,156))
    d.ellipse((360,1010,970,1530),fill=(121,205,159))
    d.ellipse((515,120,660,265),fill=(255,219,85))
    for j in range(6):
        x=70+j*115
        d.ellipse((x,850+(j%2)*35,x+55,905+(j%2)*35),fill=colors[j])
    # illustrated scene changes: clouds and playful decorative details\n    for cloud in range(3):\n        x=(75+cloud*240+step*3)%850-70\n        y=310+cloud*95\n        d.ellipse((x,y,x+130,y+58),fill=(255,255,255))\n        d.ellipse((x+28,y-30,x+100,y+52),fill=(255,255,255))\n    # animated balloon, star, or friendly animal face
    bounce=round(math.sin(step/8*math.pi*2)*30)
    cx,cy=360,560+bounce
    c=colors[i]
    if story["topic"]=="numbers":
        d.ellipse((cx-180,cy-180,cx+180,cy+180),fill=c)
        d.text((cx,cy),str(i+1),font=ImageFont.truetype(fontfile,170),anchor="mm",fill="white")
    elif story["topic"]=="animals":
        d.ellipse((cx-160,cy-130,cx+160,cy+180),fill=c)
        d.ellipse((cx-130,cy-200,cx-30,cy-80),fill=c)
        d.ellipse((cx+30,cy-200,cx+130,cy-80),fill=c)
        d.ellipse((cx-80,cy-10,cx-35,cy+35),fill=(35,48,65))
        d.ellipse((cx+35,cy-10,cx+80,cy+35),fill=(35,48,65))
        d.arc((cx-55,cy+40,cx+55,cy+120),0,180,fill=(35,48,65),width=9)
    else:
        d.ellipse((cx-170,cy-220,cx+170,cy+150),fill=c)
        d.polygon([(cx-18,cy+146),(cx+18,cy+146),(cx,cy+185)],fill=c)
        d.line((cx,cy+180,cx+20,cy+365),fill=(90,105,110),width=5)
        d.ellipse((cx-80,cy-30,cx-45,cy+5),fill=(40,45,65))
        d.ellipse((cx+45,cy-30,cx+80,cy+5),fill=(40,45,65))
        d.arc((cx-45,cy+5,cx+45,cy+80),0,180,fill=(40,45,65),width=7)
    d.text((360,115),story["title"],font=small,anchor="mm",fill=(45,65,100))
    # Child-friendly high-contrast subtitle card in the safe area\n    label=story["words"][i]\n    d.rounded_rectangle((65,920,655,1035),radius=32,fill=(255,255,255),outline=(222,232,245),width=4)\n    d.text((360,975),label,font=font,anchor="mm",fill=(40,60,95))
    return im

async def make_voice():
    await edge_tts.Communicate(story["speech"],"tr-TR-EmelNeural",rate="-10%").save(str(OUT/"voice.mp3"))
asyncio.run(make_voice())
duration=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(OUT/"voice.mp3")]).decode())
fps=12
total=math.ceil(duration*fps)
# Stream PNG frames to ffmpeg without keeping thousands of files
cmd=["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s","720x1280","-r",str(fps),"-i","-","-i",str(OUT/"voice.mp3"),"-c:v","libx264","-preset","veryfast","-crf","27","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k","-shortest",str(OUT/"video.mp4")]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
try:
    for n in range(total):
        idx=min(5,int((n/fps)/duration*6))
        p.stdin.write(frame(idx,n%24).tobytes())
finally:
    p.stdin.close()
if p.wait()!=0: raise RuntimeError("Video encoding failed")
(OUT/"caption.txt").write_text(story["title"]+" | Eğitici çocuk videosu #çocuk #eğitici #renkler",encoding="utf-8")
print("Created",OUT/"video.mp4")
