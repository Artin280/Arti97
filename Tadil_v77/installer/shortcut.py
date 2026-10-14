"""Create a Windows Unicode shell link using the supported COM interfaces."""
import ctypes,uuid
from pathlib import Path

def desktop_folder():
    buffer=ctypes.create_unicode_buffer(32768)
    result=ctypes.windll.shell32.SHGetFolderPathW(None,0x10,None,0,buffer)
    if result!=0:raise OSError('Cannot locate Desktop folder')
    return Path(buffer.value)

def create_shortcut(path,target):
    HRESULT=ctypes.c_long
    GUID=ctypes.c_ubyte*16
    def guid(value):return GUID.from_buffer_copy(uuid.UUID(value).bytes_le)
    ole=ctypes.OleDLL('ole32')
    ole.CoInitializeEx.argtypes=(ctypes.c_void_p,ctypes.c_ulong);ole.CoInitializeEx.restype=HRESULT
    status=ole.CoInitializeEx(None,2)
    if status<0:raise OSError('COM initialization failed')
    link=ctypes.c_void_p();persist=ctypes.c_void_p()
    def call(ptr,index,argtypes,*args):
        table=ctypes.cast(ptr,ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        fn=ctypes.WINFUNCTYPE(HRESULT,ctypes.c_void_p,*argtypes)(table[index])
        result=fn(ptr,*args)
        if result<0:raise OSError(f'Shortcut operation failed: {result}')
    try:
        clsid=guid('00021401-0000-0000-C000-000000000046');iid=guid('000214F9-0000-0000-C000-000000000046')
        ole.CoCreateInstance.argtypes=(ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong,ctypes.c_void_p,ctypes.c_void_p);ole.CoCreateInstance.restype=HRESULT
        result=ole.CoCreateInstance(ctypes.byref(clsid),None,1,ctypes.byref(iid),ctypes.byref(link))
        if result<0:raise OSError(f'Cannot create shortcut: {result}')
        call(link,20,(ctypes.c_wchar_p,),str(Path(target).resolve()))
        call(link,9,(ctypes.c_wchar_p,),str(Path(target).resolve().parent))
        call(link,7,(ctypes.c_wchar_p,),'Tadil v77')
        persist_iid=guid('0000010b-0000-0000-C000-000000000046')
        call(link,0,(ctypes.c_void_p,ctypes.c_void_p),ctypes.byref(persist_iid),ctypes.byref(persist))
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        call(persist,6,(ctypes.c_wchar_p,ctypes.c_int),str(Path(path).resolve()),1)
    finally:
        for pointer in (persist,link):
            if pointer.value:
                table=ctypes.cast(pointer,ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
                ctypes.WINFUNCTYPE(ctypes.c_ulong,ctypes.c_void_p)(table[2])(pointer)
        ole.CoUninitialize()
