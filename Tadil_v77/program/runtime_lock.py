"""Per-user application/install lock. Does not contain credentials or user records."""
import os
from pathlib import Path
class RuntimeLock:
    def __init__(self, app_root):self.path=Path(app_root)/'.v77-runtime.lock';self.file=None
    def acquire(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.file=self.path.open('a+b')
        if self.path.stat().st_size==0:self.file.write(b'0');self.file.flush()
        self.file.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(self.file.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            self.file.close();self.file=None
            raise RuntimeError('برنامه تعدیل یا نصب‌کننده دیگری باز است. ابتدا آن را ببندید.')
        return self
    def close(self):
        if self.file is not None:
            self.file.seek(0)
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(self.file.fileno(),msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(),fcntl.LOCK_UN)
            self.file.close();self.file=None
    def __enter__(self):return self.acquire()
    def __exit__(self,*args):self.close()
