"""Global Space hook, in-process, ctypes only.

The rule we promised: Space is swallowed *only* while the cursor is inside
Thea's silhouette. Everywhere else the key is passed straight through, so
typing in any other app is untouched.
"""

import ctypes
from ctypes import wintypes

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
VK_SPACE = 0x20

user32 = ctypes.WinDLL("user32", use_last_error=True)

LRESULT = ctypes.c_ssize_t
HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

user32.SetWindowsHookExW.restype = ctypes.c_void_p
user32.SetWindowsHookExW.argtypes = [
    ctypes.c_int,
    HOOKPROC,
    ctypes.c_void_p,
    wintypes.DWORD,
]
user32.CallNextHookEx.restype = LRESULT
user32.CallNextHookEx.argtypes = [
    ctypes.c_void_p,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
user32.UnhookWindowsHookEx.restype = wintypes.BOOL


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def cursor_pos():
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


class SpaceHook:
    def __init__(self, hit_test, on_space=None):
        self.hit_test = hit_test
        self.on_space = on_space
        self.pressed = False
        self.error = None
        self._proc = None
        self._hook = None

    def _callback(self, ncode, wparam, lparam):
        if ncode == 0 and wparam in (WM_KEYDOWN, WM_SYSKEYDOWN):
            try:
                kb = ctypes.cast(lparam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                if kb.vkCode == VK_SPACE:
                    x, y = cursor_pos()
                    if self.hit_test(x, y):
                        self.pressed = True
                        if self.on_space:
                            try:
                                self.on_space()
                            except Exception:
                                pass
                        return 1  # swallow only this key, only over Thea
            except Exception:
                pass
        return user32.CallNextHookEx(None, ncode, wparam, lparam)

    def install(self):
        if self._hook:
            return True
        self._proc = HOOKPROC(self._callback)
        self._hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._proc, None, 0)
        if not self._hook:
            self.error = ctypes.get_last_error()
            return False
        return True

    def uninstall(self):
        if self._hook:
            user32.UnhookWindowsHookEx(self._hook)
            self._hook = None
        self._proc = None
