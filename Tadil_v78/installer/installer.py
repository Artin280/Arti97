# -*- coding: utf-8 -*-
"""Offline per-user Windows installer. Backs up before publishing the new program directory."""
import os,sys,json,hashlib,zipfile,sqlite3,shutil,datetime,uuid,threading,queue,traceback,subprocess
from pathlib import Path
from runtime_lock import RuntimeLock
from shortcut import create_shortcut,desktop_folder
BUNDLE=Path(__file__).resolve().parent
TITLE='نصب تعدیل — نسخه ۷۸'

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def copy_verified(src,dest):
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
    if digest(src)!=digest(dest):raise RuntimeError('پشتیبان فایل تأیید نشد: '+str(src))

def backup_tree(src,dest):
    for path in sorted(src.rglob('*')):
        if path.is_symlink():raise RuntimeError('مسیر پیوندی در اطلاعات یافت شد: '+str(path))
        if not path.is_file():continue
        relative=path.relative_to(src);target=dest/relative
        if path.name.endswith(('-wal','-shm')) and Path(str(path).rsplit('-',1)[0]).exists():continue
        target.parent.mkdir(parents=True,exist_ok=True)
        if path.suffix.lower() in ('.db','.sqlite','.sqlite3'):
            with sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=30) as source,sqlite3.connect(target) as out:
                source.backup(out)
                if out.execute('pragma integrity_check').fetchone()[0]!='ok':raise RuntimeError('بانک پشتیبان سالم نیست: '+str(path))
        else:copy_verified(path,target)

def validate_payload(payload,manifest):
    if digest(payload)!=manifest['payload_sha256']:raise RuntimeError('بسته نصب آسیب دیده است')
    with zipfile.ZipFile(payload) as archive:
        names=archive.namelist()
        if len(set(names))!=len(names) or set(names)!=set(manifest['files']):raise RuntimeError('فهرست فایل‌های نصب معتبر نیست')
        for name in names:
            normalized=Path(name.replace('\\','/'))
            if normalized.is_absolute() or '..' in normalized.parts or ':' in name:raise RuntimeError('مسیر نامعتبر در بسته')
            if hashlib.sha256(archive.read(name)).hexdigest()!=manifest['files'][name]:raise RuntimeError('فایل نصب آسیب دیده است: '+name)

def install(app_root=None,shortcut_path=None,progress=lambda text:None):
    root=Path(app_root or Path(os.environ['LOCALAPPDATA'])/'TadilApp').resolve()
    root.mkdir(parents=True,exist_ok=True)
    payload=BUNDLE/'application.zip';manifest=json.loads((BUNDLE/'manifest.json').read_text(encoding='utf-8'))
    progress('بررسی سلامت بسته نصب…');validate_payload(payload,manifest)
    stage=root/('.stage-v78-'+uuid.uuid4().hex);dest=root/'program_v78'
    with RuntimeLock(root):
        # Estimated staging, backup and extraction space. Data is never replaced.
        retained=[p for p in root.iterdir() if p.is_dir() and (p.name=='data' or p.name.startswith('program_v'))]
        required=sum(p.stat().st_size for d in retained for p in d.rglob('*') if p.is_file())+manifest['unpacked_bytes']*2+10*1024*1024
        if shutil.disk_usage(root).free<required:raise RuntimeError('فضای آزاد برای پشتیبان و نصب کافی نیست')
        stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        backup=root/'installer_backups'/('v78_'+stamp);backup.mkdir(parents=True,exist_ok=False)
        progress('تهیه و بررسی پشتیبان اطلاعات و نسخه‌های قبلی…')
        for directory in retained:backup_tree(directory,backup/directory.name)
        backups={str(p.relative_to(backup)):digest(p) for p in backup.rglob('*') if p.is_file()}
        (backup/'backup-manifest.json').write_text(json.dumps(backups,ensure_ascii=False,indent=2),encoding='utf-8')
        progress('نصب برنامه مستقل نسخه ۷۸…')
        stage.mkdir()
        try:
            with zipfile.ZipFile(payload) as archive:archive.extractall(stage)
            for name,expected in manifest['files'].items():
                if digest(stage/name)!=expected:raise RuntimeError('فایل استخراج‌شده معتبر نیست: '+name)
            executable=stage/'Tadil_v78.exe'
            if not executable.is_file():raise RuntimeError('فایل اجرایی در بسته وجود ندارد')
            shortcut=Path(shortcut_path) if shortcut_path else desktop_folder()/'Tadil v78.lnk'
            previous_shortcut=shortcut.read_bytes() if shortcut.exists() else None
            if previous_shortcut is not None:
                (backup/'previous-shortcut.lnk').write_bytes(previous_shortcut)
            old=backup/'program_v78_replaced'
            moved=False;published=False
            try:
                if dest.exists():dest.rename(old);moved=True
                stage.rename(dest);published=True
                progress('ساخت میان‌بر روی دسکتاپ…')
                create_shortcut(shortcut,dest/'Tadil_v78.exe')
                if not shortcut.is_file():raise RuntimeError('میان‌بر ایجاد نشد')
                record={'version':78,'backup':str(backup),'program':str(dest),'shortcut':str(shortcut),'installed_at':datetime.datetime.now().isoformat()}
                temporary=root/'installed_v78.json.tmp';temporary.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(temporary,root/'installed_v78.json')
            except Exception:
                if published:dest.rename(backup/'failed_new_program')
                if moved:old.rename(dest)
                if previous_shortcut is not None:shortcut.write_bytes(previous_shortcut)
                elif shortcut.exists():shortcut.unlink()
                raise
        except Exception:
            if stage.exists():shutil.rmtree(stage)
            raise
    progress('نصب پایان یافت؛ اطلاعات قبلی در محل خود باقی مانده‌اند.')
    return record

def main():
    if '--quiet' in sys.argv:
        result=install()
        print(json.dumps(result,ensure_ascii=False));return
    import tkinter as tk
    from tkinter import ttk,messagebox
    root=tk.Tk();root.title(TITLE);root.geometry('620x340');root.resizable(False,False)
    root.option_add('*Font',('Tahoma',10));root.configure(background='#e9f1fb')
    tk.Label(root,text='سامانه محاسبه تعدیل — نسخه ۷۸',font=('Tahoma',16,'bold'),fg='#06427c',bg='#e9f1fb').pack(pady=20)
    tk.Label(root,text='ابتدا نسخه‌های باز برنامه را ببندید.\nنصب پیش از هر تغییر پشتیبان می‌گیرد و اطلاعات قبلی را حفظ می‌کند.\nنیازی به نصب Python، اینترنت یا ویرایش کد ندارید.',justify='right',bg='#e9f1fb').pack(pady=8)
    status=tk.StringVar(value='آماده نصب');ttk.Label(root,textvariable=status,wraplength=570,justify='right').pack(pady=15)
    bar=ttk.Progressbar(root,mode='indeterminate',length=540);bar.pack(pady=5)
    messages=queue.Queue();busy={'value':False};buttons=ttk.Frame(root);buttons.pack(pady=16)
    def close():
        if not busy['value']:root.destroy()
    root.protocol('WM_DELETE_WINDOW',close)
    def begin():
        busy['value']=True;button.configure(state='disabled');bar.start()
        def worker():
            try:messages.put(('done',install(progress=lambda value:messages.put(('status',value)))))
            except Exception:messages.put(('error',traceback.format_exc()))
        threading.Thread(target=worker,daemon=True).start()
    button=ttk.Button(buttons,text='نصب نسخه ۷۸',command=begin);button.pack(side='right',padx=8)
    ttk.Button(buttons,text='بستن',command=close).pack(side='left',padx=8)
    def poll():
        try:
            while True:
                kind,value=messages.get_nowait()
                if kind=='status':status.set(value)
                else:
                    bar.stop();busy['value']=False
                    if kind=='done':
                        status.set('نصب موفق بود؛ میان‌بر Tadil v78 روی دسکتاپ ساخته شد.')
                        messagebox.showinfo(TITLE,'نصب انجام شد.\nبرای اجرا روی Tadil v78 در دسکتاپ دوبار کلیک کنید.\n\nپشتیبان:\n'+value['backup'],parent=root)
                        button.configure(text='اجرای برنامه',state='normal',command=lambda:subprocess.Popen([str(Path(value['program'])/'Tadil_v78.exe')],cwd=value['program']))
                    else:
                        status.set('نصب متوقف شد؛ جزئیات خطا را بررسی کنید.')
                        button.configure(state='normal')
                        messagebox.showerror(TITLE,value[-1800:],parent=root)
        except queue.Empty:pass
        root.after(100,poll)
    poll();root.mainloop()

if __name__=='__main__':
    try:main()
    except Exception:
        error=traceback.format_exc()
        if '--quiet' in sys.argv:
            print(error);sys.exit(1)
        try:
            import tkinter as tk
            from tkinter import messagebox
            messagebox.showerror(TITLE,error[-1800:])
        except Exception:pass
        sys.exit(1)
