import sys,glob
from PIL import Image
fs=sorted(glob.glob(sys.argv[1]+'/*.png')); sc=int(sys.argv[3]) if len(sys.argv)>3 else 2
W=128*sc; Hh=160*sc; cols=min(len(fs),5); rows=(len(fs)+cols-1)//cols
sh=Image.new('RGB',(cols*(W+8),rows*(Hh+8)),(70,90,70))
for i,f in enumerate(fs):
    im=Image.open(f).resize((W,Hh),Image.NEAREST)
    bg=Image.new('RGBA',im.size,(120,140,120,255)); bg.alpha_composite(im)
    sh.paste(bg.convert('RGB'),((i%cols)*(W+8),(i//cols)*(Hh+8)))
sh.save(sys.argv[2])
