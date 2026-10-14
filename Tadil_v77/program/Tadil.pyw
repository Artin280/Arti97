# -*- coding: utf-8 -*-
"""Version 77 launcher, isolated smoke check, callback diagnostics and single-instance lock."""
import os,sys,traceback,datetime,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def alert(message):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None,str(message),'Tadil v77',0x10)
    except Exception:pass

def smoke_test(path):
    # Explicit QA mode creates only a synthetic dataset under the requested directory.
    root=Path(path).resolve();root.mkdir(parents=True,exist_ok=True)
    os.environ['LOCALAPPDATA']=str(root)
    import tadil_app_v77 as app
    app.DB.parent.mkdir(parents=True,exist_ok=True)
    for name in ('showinfo','showwarning'):setattr(app.messagebox,name,lambda *a,**kw:None)
    def error(*a,**kw):raise RuntimeError(str(a))
    app.messagebox.showerror=error
    app.messagebox.askyesno=lambda *a,**kw:True
    app.messagebox.askyesnocancel=lambda *a,**kw:True
    with app.db() as c:
        c.execute("insert or replace into selected values(1,'فاضلاب','1','TEST')")
        c.execute("insert or replace into amounts values(1,'فاضلاب|1',1250)")
        c.execute("insert or replace into statements values(1,'','','')")
    a=app.App();a.update()
    a.vars['project'].set('PACKAGED GUI SMOKE TEST')
    row=a.tree.get_children()[0];a.tree.set(row,'cur','2500');a.save_stmt()
    a.new_statement();a.update()
    assert a.sno.get()==2
    assert a.tree.set(a.tree.get_children()[0],'prev')=='2500'
    a.ss.set('1397/01/01');a.se.set('1397/01/31');a.sd.set('1397/02/01')
    rows=a.calculate();assert rows
    opened=[];a.open_file=lambda p:opened.append(Path(p));a.print_calc();a.print_cover()
    assert len(opened)==2 and all(p.is_file() for p in opened)
    for index,button in enumerate(a.nav_buttons):
        button.invoke();a.update();assert a.nb.index(a.nb.select())==index
    a._close_safely()
    b=app.App();b.update()
    assert b.vars['project'].get()=='PACKAGED GUI SMOKE TEST'
    assert b.sno.get()==2 and len(b.ct.get_children())==len(rows)
    b._close_safely()
    (root/'results.json').write_text(json.dumps({'ok':True,'version':77,'rows':len(rows),'platform':sys.platform,'tests':['real GUI init','draft amount save','new statement','previous amount','calculation','A4 HTML outputs','five navigation buttons','close and reopen']},ensure_ascii=False,indent=2),encoding='utf-8')

def verify_smoke(path):
    root=Path(path).resolve();os.environ['LOCALAPPDATA']=str(root)
    import tadil_app_v77 as app
    expected=json.loads((root/'results.json').read_text(encoding='utf-8'))
    for name in ('showinfo','showwarning'):setattr(app.messagebox,name,lambda *a,**kw:None)
    def error(*a,**kw):raise RuntimeError(str(a))
    app.messagebox.showerror=error
    a=app.App();a.update()
    assert a.vars['project'].get()=='PACKAGED GUI SMOKE TEST'
    assert a.sno.get()==2 and len(a.ct.get_children())==expected['rows']
    assert a.c.execute("select current from amounts where stmt=1 and itemkey='فاضلاب|1'").fetchone()[0]==2500
    assert a.ss.get()=='1397/01/01' and a.se.get()=='1397/01/31' and a.sd.get()=='1397/02/01'
    a._close_safely()
    (root/'verified.json').write_text(json.dumps({'ok':True,'version':77,'test':'separate executable process restores metadata, dates, amounts and calculation snapshot'},ensure_ascii=False),encoding='utf-8')

test_flag=next((flag for flag in ('--smoke-test','--verify-saved-smoke') if flag in sys.argv),None)
if test_flag:
    try:
        path=sys.argv[sys.argv.index(test_flag)+1]
        (smoke_test if test_flag=='--smoke-test' else verify_smoke)(path)
    except Exception:
        target=Path(sys.argv[sys.argv.index(test_flag)+1]);target.mkdir(parents=True,exist_ok=True)
        (target/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');sys.exit(1)
    sys.exit(0)

LOG=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'TadilApp'/'Tadil-startup.log'
LOG.parent.mkdir(parents=True,exist_ok=True)
def write(message):
    with LOG.open('a',encoding='utf-8') as f:f.write(datetime.datetime.now().isoformat()+' '+message+'\n')
try:
    from runtime_lock import RuntimeLock
    with RuntimeLock(LOG.parent):
        os.chdir(Path(sys.executable).parent if getattr(sys,'frozen',False) else HERE)
        write('v77 startup')
        import tkinter as tk
        import tadil_app_v77
        original=tk.Tk.__init__
        def patched(self,*args,**kwargs):
            original(self,*args,**kwargs)
            def report(exc,val,tb):
                write('Callback error: '+''.join(traceback.format_exception(exc,val,tb)))
                alert('خطا در برنامه؛ جزئیات در فایل زیر ثبت شد:\n'+str(LOG)+'\n'+str(val))
            self.report_callback_exception=report
        tk.Tk.__init__=patched
        tadil_app_v77.start_manager()
except Exception:
    detail=traceback.format_exc();write('FATAL: '+detail)
    alert('اجرای تعدیل متوقف شد:\n'+detail.splitlines()[-1]+'\n\nگزارش: '+str(LOG))
    sys.exit(1)
