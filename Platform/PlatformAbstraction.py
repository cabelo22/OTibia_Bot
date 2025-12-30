"""
Multi-platform abstraction layer for Windows and Linux support.
Provides unified interface for memory operations, window management, and input simulation.
"""

import platform
import sys

PLATFORM = platform.system()
IS_WINDOWS = PLATFORM == 'Windows'
IS_LINUX = PLATFORM == 'Linux'

# Platform-specific imports
if IS_WINDOWS:
    try:
        import win32api
        import win32con
        import win32gui
        import win32ui
        import win32security
        import win32process
    except ImportError:
        print("ERROR: pywin32 not installed. Run: pip install pywin32")
        sys.exit(1)
else:  # Linux
    try:
        from Xlib import X, display, protocol
        from Xlib.ext import xtest
    except ImportError:
        print("ERROR: python-xlib not installed. Run: pip install python-xlib")
        sys.exit(1)

import ctypes as c
from ctypes import c_void_p, c_size_t, c_int, c_uint, c_long, c_ulong, POINTER, byref


# ============================================================================
# MEMORY OPERATIONS
# ============================================================================

class MemoryAPI:
    """Cross-platform memory operations"""
    
    def __init__(self):
        if IS_WINDOWS:
            self.kernel32 = c.windll.kernel32
        else:  # Linux
            self.libc = c.CDLL('libc.so.6')
            # Linux process_vm_readv for memory reading
            self.libc.process_vm_readv.argtypes = [
                c_int,  # pid
                POINTER(c.c_void_p),  # local_iov
                c_ulong,  # liovcnt
                POINTER(c.c_void_p),  # remote_iov
                c_ulong,  # riovcnt
                c_ulong   # flags
            ]
            self.libc.process_vm_readv.restype = c.c_ssize_t
    
    def read_process_memory(self, process_handle, address, buffer, size):
        """Read memory from a process"""
        if IS_WINDOWS:
            result = self.kernel32.ReadProcessMemory(
                process_handle, 
                c_void_p(address), 
                buffer, 
                size, 
                byref(c_size_t())
            )
            return bool(result)
        else:  # Linux
            # Linux implementation using process_vm_readv
            pid = process_handle  # On Linux, we use PID directly
            
            # Setup iovec structures
            class iovec(c.Structure):
                _fields_ = [
                    ("iov_base", c_void_p),
                    ("iov_len", c_size_t)
                ]
            
            local = iovec(c.cast(buffer, c_void_p), size)
            remote = iovec(c_void_p(address), size)
            
            result = self.libc.process_vm_readv(
                pid,
                byref(local), 1,
                byref(remote), 1,
                0
            )
            return result == size
    
    def open_process(self, pid):
        """Open a process and return handle"""
        if IS_WINDOWS:
            PROCESS_ALL_ACCESS = 0x1F0FFF
            return self.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        else:  # Linux
            # On Linux, we just return the PID
            # No handle needed, process_vm_readv uses PID directly
            return pid
    
    def enable_debug_privilege(self):
        """Enable debug privileges (Windows only)"""
        if IS_WINDOWS:
            try:
                hToken = win32security.OpenProcessToken(
                    win32api.GetCurrentProcess(),
                    win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY
                )
                privilege_id = win32security.LookupPrivilegeValue(None, win32security.SE_DEBUG_NAME)
                win32security.AdjustTokenPrivileges(hToken, False, [(privilege_id, win32con.SE_PRIVILEGE_ENABLED)])
                return True
            except Exception as e:
                print(f"Failed to enable debug privilege: {e}")
                return False
        # Linux doesn't need this, requires ptrace permissions instead
        return True


# ============================================================================
# WINDOW MANAGEMENT
# ============================================================================

class WindowAPI:
    """Cross-platform window management"""
    
    def __init__(self):
        if IS_LINUX:
            self.display = display.Display()
    
    def find_window(self, window_title=None, class_name=None):
        """Find window by title or class name"""
        if IS_WINDOWS:
            return win32gui.FindWindow(class_name, window_title)
        else:  # Linux
            root = self.display.screen().root
            window_ids = root.get_full_property(
                self.display.intern_atom('_NET_CLIENT_LIST'),
                X.AnyPropertyType
            ).value
            
            for window_id in window_ids:
                window = self.display.create_resource_object('window', window_id)
                title = window.get_wm_name()
                if window_title and title == window_title:
                    return window_id
            return None
    
    def get_window_rect(self, hwnd):
        """Get window rectangle (left, top, right, bottom)"""
        if IS_WINDOWS:
            return win32gui.GetWindowRect(hwnd)
        else:  # Linux
            window = self.display.create_resource_object('window', hwnd)
            geom = window.get_geometry()
            return (geom.x, geom.y, geom.x + geom.width, geom.y + geom.height)
    
    def is_window_visible(self, hwnd):
        """Check if window is visible"""
        if IS_WINDOWS:
            return win32gui.IsWindowVisible(hwnd)
        else:  # Linux
            window = self.display.create_resource_object('window', hwnd)
            attrs = window.get_attributes()
            return attrs.map_state == X.IsViewable
    
    def get_window_text(self, hwnd):
        """Get window title"""
        if IS_WINDOWS:
            return win32gui.GetWindowText(hwnd)
        else:  # Linux
            window = self.display.create_resource_object('window', hwnd)
            return window.get_wm_name() or ""
    
    def enum_windows(self, callback):
        """Enumerate all windows"""
        if IS_WINDOWS:
            win32gui.EnumWindows(callback, None)
        else:  # Linux
            root = self.display.screen().root
            window_list = root.get_full_property(
                self.display.intern_atom('_NET_CLIENT_LIST'),
                X.AnyPropertyType
            )
            if window_list:
                for window_id in window_list.value:
                    callback(window_id, None)
    
    def get_window_thread_process_id(self, hwnd):
        """Get process ID from window handle"""
        if IS_WINDOWS:
            return win32process.GetWindowThreadProcessId(hwnd)
        else:  # Linux
            window = self.display.create_resource_object('window', hwnd)
            pid_property = window.get_full_property(
                self.display.intern_atom('_NET_WM_PID'),
                X.AnyPropertyType
            )
            if pid_property:
                pid = pid_property.value[0]
                return (0, pid)  # Return (thread_id, process_id) - thread_id not used on Linux
            return (0, 0)


# ============================================================================
# INPUT SIMULATION
# ============================================================================

class InputAPI:
    """Cross-platform input simulation"""
    
    # Message constants
    WM_MOUSEMOVE = 0x0200
    WM_LBUTTONDOWN = 0x0201
    WM_LBUTTONUP = 0x0202
    WM_RBUTTONDOWN = 0x0204
    WM_RBUTTONUP = 0x0205
    WM_KEYDOWN = 0x0100
    WM_KEYUP = 0x0101
    
    def __init__(self):
        if IS_LINUX:
            self.display = display.Display()
    
    def post_message(self, hwnd, msg, wparam, lparam):
        """Post message to window"""
        if IS_WINDOWS:
            return win32gui.PostMessage(hwnd, msg, wparam, lparam)
        else:  # Linux
            # On Linux, we use XTest extension to simulate input
            window = self.display.create_resource_object('window', hwnd)
            
            # Extract coordinates from lparam
            x = lparam & 0xFFFF
            y = (lparam >> 16) & 0xFFFF
            
            # Map Windows messages to X11 events
            if msg == self.WM_MOUSEMOVE:
                xtest.fake_input(self.display, X.MotionNotify, x=x, y=y)
            elif msg == self.WM_LBUTTONDOWN:
                xtest.fake_input(self.display, X.ButtonPress, 1)
            elif msg == self.WM_LBUTTONUP:
                xtest.fake_input(self.display, X.ButtonRelease, 1)
            elif msg == self.WM_RBUTTONDOWN:
                xtest.fake_input(self.display, X.ButtonPress, 3)
            elif msg == self.WM_RBUTTONUP:
                xtest.fake_input(self.display, X.ButtonRelease, 3)
            elif msg == self.WM_KEYDOWN:
                keycode = self.display.keysym_to_keycode(wparam)
                xtest.fake_input(self.display, X.KeyPress, keycode)
            elif msg == self.WM_KEYUP:
                keycode = self.display.keysym_to_keycode(wparam)
                xtest.fake_input(self.display, X.KeyRelease, keycode)
            
            self.display.sync()
            return True
    
    def make_long(self, low, high):
        """Combine two 16-bit values into 32-bit long"""
        return (high << 16) | (low & 0xFFFF)
    
    def get_async_key_state(self, vkey):
        """Get async key state"""
        if IS_WINDOWS:
            return win32api.GetAsyncKeyState(vkey)
        else:  # Linux
            # On Linux, query keyboard state
            keys = self.display.query_keymap()
            keycode = self.display.keysym_to_keycode(vkey)
            if keycode < len(keys) * 8:
                byte_index = keycode // 8
                bit_index = keycode % 8
                return (keys[byte_index] & (1 << bit_index)) != 0
            return 0
    
    def get_cursor_pos(self):
        """Get cursor position"""
        if IS_WINDOWS:
            return win32api.GetCursorPos()
        else:  # Linux
            data = self.display.screen().root.query_pointer()
            return (data.root_x, data.root_y)
    
    def screen_to_client(self, hwnd, pos):
        """Convert screen coordinates to client coordinates"""
        if IS_WINDOWS:
            return win32gui.ScreenToClient(hwnd, pos)
        else:  # Linux
            window = self.display.create_resource_object('window', hwnd)
            geom = window.get_geometry()
            return (pos[0] - geom.x, pos[1] - geom.y)


# ============================================================================
# SCREEN CAPTURE
# ============================================================================

class ScreenCaptureAPI:
    """Cross-platform screen capture"""
    
    def __init__(self):
        if IS_LINUX:
            self.display = display.Display()
    
    def capture_window(self, hwnd, x, y, w, h):
        """Capture window region and return as numpy array"""
        if IS_WINDOWS:
            import numpy as np
            from PIL import Image
            
            wDC = win32gui.GetWindowDC(hwnd)
            dc_obj = win32ui.CreateDCFromHandle(wDC)
            cDC = dc_obj.CreateCompatibleDC()
            data_bitmap = win32ui.CreateBitmap()
            data_bitmap.CreateCompatibleBitmap(dc_obj, w, h)
            cDC.SelectObject(data_bitmap)
            cDC.BitBlt((0, 0), (w, h), dc_obj, (x, y), win32con.SRCCOPY)
            
            signed_ints_array = data_bitmap.GetBitmapBits(True)
            img = np.frombuffer(signed_ints_array, dtype='uint8')
            img.shape = (h, w, 4)
            
            # Cleanup
            dc_obj.DeleteDC()
            cDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, wDC)
            win32gui.DeleteObject(data_bitmap.GetHandle())
            
            return img
        else:  # Linux
            import numpy as np
            from PIL import Image
            
            window = self.display.create_resource_object('window', hwnd)
            geom = window.get_geometry()
            
            # Capture the window
            raw = window.get_image(x, y, w, h, X.ZPixmap, 0xffffffff)
            image = Image.frombytes("RGB", (w, h), raw.data, "raw", "BGRX")
            
            # Convert to numpy array
            img = np.array(image)
            return img


# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

memory_api = MemoryAPI()
window_api = WindowAPI()
input_api = InputAPI()
screen_api = ScreenCaptureAPI()


# ============================================================================
# COMPATIBILITY WRAPPERS
# ============================================================================

# For backward compatibility with existing code
if IS_WINDOWS:
    # Export win32 modules directly on Windows
    pass
else:
    # Create compatibility shims for Linux
    class Win32ConCompat:
        """Compatibility class for win32con constants"""
        # Window messages
        WM_MOUSEMOVE = InputAPI.WM_MOUSEMOVE
        WM_LBUTTONDOWN = InputAPI.WM_LBUTTONDOWN
        WM_LBUTTONUP = InputAPI.WM_LBUTTONUP
        WM_RBUTTONDOWN = InputAPI.WM_RBUTTONDOWN
        WM_RBUTTONUP = InputAPI.WM_RBUTTONUP
        WM_KEYDOWN = InputAPI.WM_KEYDOWN
        WM_KEYUP = InputAPI.WM_KEYUP
        
        # Other constants
        SRCCOPY = 0x00CC0020
        TOKEN_ADJUST_PRIVILEGES = 0x0020
        TOKEN_QUERY = 0x0008
        SE_PRIVILEGE_ENABLED = 0x00000002
        
        # Virtual key codes (common ones)
        VK_LBUTTON = 0x01
        VK_RETURN = 0x0D
        VK_SHIFT = 0x10
        VK_CONTROL = 0x11
        VK_MENU = 0x12  # Alt key
    
    class Win32ApiCompat:
        """Compatibility class for win32api functions"""
        @staticmethod
        def MAKELONG(low, high):
            return input_api.make_long(low, high)
        
        @staticmethod
        def GetAsyncKeyState(vkey):
            return input_api.get_async_key_state(vkey)
        
        @staticmethod
        def GetCursorPos():
            return input_api.get_cursor_pos()
        
        @staticmethod
        def GetCurrentProcess():
            import os
            return os.getpid()
    
    class Win32GuiCompat:
        """Compatibility class for win32gui functions"""
        @staticmethod
        def FindWindow(class_name, window_title):
            return window_api.find_window(window_title, class_name)
        
        @staticmethod
        def GetWindowRect(hwnd):
            return window_api.get_window_rect(hwnd)
        
        @staticmethod
        def IsWindowVisible(hwnd):
            return window_api.is_window_visible(hwnd)
        
        @staticmethod
        def GetWindowText(hwnd):
            return window_api.get_window_text(hwnd)
        
        @staticmethod
        def EnumWindows(callback, data):
            return window_api.enum_windows(callback)
        
        @staticmethod
        def PostMessage(hwnd, msg, wparam, lparam):
            return input_api.post_message(hwnd, msg, wparam, lparam)
        
        @staticmethod
        def ScreenToClient(hwnd, pos):
            return input_api.screen_to_client(hwnd, pos)
        
        @staticmethod
        def GetWindowDC(hwnd):
            return hwnd  # Dummy for compatibility
        
        @staticmethod
        def ReleaseDC(hwnd, hdc):
            pass  # Dummy for compatibility
        
        @staticmethod
        def DeleteObject(hobj):
            pass  # Dummy for compatibility
    
    # Export compatibility modules
    win32con = Win32ConCompat()
    win32api = Win32ApiCompat()
    win32gui = Win32GuiCompat()
