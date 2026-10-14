# -*- coding: utf-8 -*-
"""Stable silent Windows launcher; records all startup errors."""
import os,sys,traceback,datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent
LOG=Path(os.environ.get('LOCALAPPDATA',str(HERE)))/'TadilApp'/'Tadil-startup.log'
LOG.parent.mkdir(parents=True,exist_ok=True)
def write(s):
    with LOG.open('a',encoding='utf-8') as f: f.write(datetime.datetime.now().isoformat()+' '+s+'\n')
def alert(s):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None,s,'Tadil - Error',0x10)
    except Exception: pass
try:
    os.chdir(HERE)
    write('v76 startup; '+sys.executable)
    import tkinter as tk
    import tadil_app_v76
    original=tk.Tk.__init__
    def patched(self,*args,**kwargs):
        original(self,*args,**kwargs)
        def report(exc,val,tb):
            write('Callback error: '+''.join(traceback.format_exception(exc,val,tb)))
            alert('Program error. Log: '+str(LOG)+'\n'+str(val))
        self.report_callback_exception=report
    tk.Tk.__init__=patched
    tadil_app_v76.start_manager()
except BaseException:
    detail=traceback.format_exc()
    write('FATAL: '+detail)
    alert('Tadil failed. Log: '+str(LOG)+'\n'+detail[-350:])
