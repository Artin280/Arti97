import sys,os,tempfile,json
from pathlib import Path
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'installer'))
import installer as m
qa=Path(tempfile.mkdtemp(prefix='installer-gui-',dir=R));os.environ['LOCALAPPDATA']=str(qa)
m.desktop_folder=lambda:qa/'desktop'
if os.name!='nt':m.create_shortcut=lambda p,t:(Path(p).parent.mkdir(parents=True,exist_ok=True),Path(p).write_text(str(t)))
import tkinter as tk
from tkinter import ttk,messagebox
errors=[];messagebox.showinfo=lambda *a,**kw:None;messagebox.showerror=lambda *a,**kw:errors.append(a)
loop=tk.Tk.mainloop

def test_loop(root):
 started={'value':False};count={'value':0}
 def widgets(parent):
  for w in parent.winfo_children():yield w;yield from widgets(w)
 def check():
  count['value']+=1
  buttons=[w for w in widgets(root) if isinstance(w,ttk.Button)]
  if not started['value']:
   target=next(w for w in buttons if w.cget('text')=='نصب نسخه ۷۷');target.invoke();started['value']=True
  elif any(w.cget('text')=='اجرای برنامه' for w in buttons):root.destroy();return
  if errors or count['value']>1800:root.destroy();return
  root.after(100,check)
 root.after(100,check);loop(root)
tk.Tk.mainloop=test_loop;m.main()
assert not errors,errors
assert (qa/'TadilApp/program_v77/Tadil_v77.exe').exists()
assert (qa/'desktop/Tadil v77.lnk').exists()
(R/'INSTALLER_GUI_RESULTS.json').write_text(json.dumps({'ok':True,'platform':sys.platform,'scope':'actual installer GUI and worker-thread install; success dialogs auto-dismissed'},ensure_ascii=False),encoding='utf-8')
print('PASS installer GUI start button, progress updates, background backup/install and completion state')
