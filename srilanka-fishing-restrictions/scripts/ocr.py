import sys, fitz, os, time
from rapidocr_onnxruntime import RapidOCR
eng = RapidOCR()
for pid in sys.argv[1:]:
    src=f'/workspace/fishing-restrictions/raw/gazettes/dfar_{pid}.pdf'
    out=f'/workspace/fishing-restrictions/raw/gazettes/dfar_{pid}.ocr.txt'
    if os.path.exists(out): continue
    t=time.time(); doc=fitz.open(src); parts=[]
    for i,p in enumerate(doc):
        pix=p.get_pixmap(dpi=int(os.environ.get("OCR_DPI","200"))); img=pix.tobytes('png')
        res,_=eng(img)
        lines=[]
        if res:
            # sort by y then x
            res=sorted(res,key=lambda r:(round(r[0][0][1]/15),r[0][0][0]))
            lines=[r[1] for r in res]
        parts.append(f'--- page {i+1}\n'+'\n'.join(lines))
    open(out,'w').write('\n'.join(parts)); print(pid,len(doc),round(time.time()-t),'s',flush=True)
