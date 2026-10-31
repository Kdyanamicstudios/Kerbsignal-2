"""Export the actual startup painter as a looping GIF and H.264 preview."""
from pathlib import Path
import sys,subprocess
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parents[1]/'race_engineer')]
from PIL import Image
from render_drive_preview import PillowCanvas
from engineer.startup import WIDTH,HEIGHT,paint_startup

ROOT=Path(__file__).resolve().parents[1]
class Canvas(PillowCanvas):
    def create_image(self,x,y,**kw):
        im=kw['image'];self.image.paste(im,(round(x-im.width/2),round(y-im.height/2)),im)
logo=Image.open(ROOT/'race_engineer/engineer/assets/kerbsignal-128.png').convert('RGBA')
frames=[]
for i in range(43):
    c=Canvas(WIDTH,HEIGHT);paint_startup(c,logo,min(1,i/42));frames.append(c.image)
frames[0].save(ROOT/'KerbSignal_Startup_Animation.gif',save_all=True,append_images=frames[1:],duration=[33]*42+[700],loop=0,disposal=2)
process=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{WIDTH}x{HEIGHT}','-r','30','-i','pipe:0','-an','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(ROOT/'KerbSignal_Startup_Animation.mp4')],stdin=subprocess.PIPE)
for im in frames+[frames[-1]]*20:process.stdin.write(im.tobytes())
process.stdin.close();assert process.wait()==0
# Contact sheet for visual inspection, kept as a temporary QA image.
sheet=Image.new('RGB',(WIDTH*3,HEIGHT))
for j,i in enumerate((0,10,42)):sheet.paste(frames[i],(j*WIDTH,0))
sheet.save(ROOT/'windows_build/startup_contact_sheet.png')
print('Exported startup GIF and MP4 using the production painter.')
