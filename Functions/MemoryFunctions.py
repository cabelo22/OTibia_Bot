import Addresses
import ctypes as c
import struct
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Platform.PlatformAbstraction import memory_api, IS_WINDOWS

if IS_WINDOWS:
    import win32api
    import win32con
    import win32security

# Structure for VirtualQueryEx
class MEMORY_BASIC_INFORMATION(c.Structure):
    _fields_ = [
        ("BaseAddress", c.c_void_p),
        ("AllocationBase", c.c_void_p),
        ("AllocationProtect", c.c_uint32),
        ("RegionSize", c.c_size_t),
        ("State", c.c_uint32),
        ("Protect", c.c_uint32),
        ("Type", c.c_uint32),
    ]



# Reads value from memory
def read_memory_address(address_read, offsets, option):
    try:
        address = c.c_void_p(Addresses.base_address + address_read + offsets)
        if option < 6:
            buffer_size = int(Addresses.application_architecture/8)
        else:
            buffer_size = 32
        buffer = c.create_string_buffer(buffer_size)
        result = memory_api.read_process_memory(Addresses.process_handle, address, buffer, buffer_size)
        if not result:
            return None
        match option:
            case 1:
                return c.cast(buffer, c.POINTER(c.c_byte)).contents.value
            case 2:
                return c.cast(buffer, c.POINTER(c.c_short)).contents.value
            case 3:
                return c.cast(buffer, c.POINTER(c.c_int)).contents.value
            case 4:
                return c.cast(buffer, c.POINTER(c.c_ulonglong)).contents.value
            case 5:
                return c.cast(buffer, c.POINTER(c.c_double)).contents.value
            case 6:
                try:
                    decoded_value = buffer.value.decode('utf-8')
                except UnicodeDecodeError:
                    decoded_value = "*"
                return decoded_value
            case 7:
                try:
                    decoded_value = buffer.raw.decode('utf-16').split('\x00')[0]
                except UnicodeDecodeError:
                    decoded_value = "*"
                return decoded_value
            case _:
                return bytes(buffer)
    except Exception as e:
        print('Memory Exception:', e)
        return None


def read_pointer_address(address_read, offsets, option):
    try:
        address = c.c_void_p(Addresses.base_address + address_read)
        if option == 6 or option == 7:
            buffer_size = 64
        else:
            buffer_size = int(Addresses.application_architecture/8)
        buffer = c.create_string_buffer(buffer_size)
        for offset in offsets:
            result = memory_api.read_process_memory(Addresses.process_handle, address, buffer, buffer_size)
            if not result:
                return None
            if buffer_size == 4:
                address = c.c_void_p(c.cast(buffer, c.POINTER(c.c_int)).contents.value + offset)
            else:
                address = c.c_void_p(c.cast(buffer, c.POINTER(c.c_longlong)).contents.value + offset)
        result = memory_api.read_process_memory(Addresses.process_handle, address, buffer, buffer_size)
        if not result:
            return None
        match option:
            case 1:
                return c.cast(buffer, c.POINTER(c.c_byte)).contents.value
            case 2:
                return c.cast(buffer, c.POINTER(c.c_short)).contents.value
            case 3:
                return c.cast(buffer, c.POINTER(c.c_int)).contents.value
            case 4:
                return c.cast(buffer, c.POINTER(c.c_ulonglong)).contents.value
            case 5:
                return c.cast(buffer, c.POINTER(c.c_double)).contents.value
            case 6:
                try:
                    decoded_value = buffer.value.decode('utf-8')
                except UnicodeDecodeError:
                    decoded_value = "*"
                return decoded_value
            case 7:
                try:
                    decoded_value = buffer.raw.decode('utf-16').split('\x00')[0]
                except UnicodeDecodeError:
                    decoded_value = "*"
                return decoded_value
            case _:
                return bytes(buffer)
    except Exception as e:
        print('Pointer Exception:', e)
        return None


def read_targeting_status():
    if Addresses.attack_address_offset == [-1]:
        # Case where Attack Address holds the ID directly
        attack_id = read_memory_address(Addresses.attack_address, 0, Addresses.my_attack_type)
        return attack_id if attack_id and attack_id > 0 else 0
    else:
        # Standard pointer case
        attack = read_pointer_address(Addresses.attack_address, Addresses.attack_address_offset, Addresses.my_attack_type)
        return attack


def read_my_stats():
    current_hp = read_pointer_address(Addresses.my_stats_address, Addresses.my_hp_offset, Addresses.my_hp_type)
    current_max_hp = read_pointer_address(Addresses.my_stats_address, Addresses.my_hp_max_offset, Addresses.my_hp_type)
    current_mp = read_pointer_address(Addresses.my_stats_address, Addresses.my_mp_offset, Addresses.my_mp_type)
    current_max_mp = read_pointer_address(Addresses.my_stats_address, Addresses.my_mp_max_offset, Addresses.my_mp_type)
    return current_hp, current_max_hp, current_mp, current_max_mp


def read_my_wpt():
    x = read_pointer_address(Addresses.my_x_address, Addresses.my_x_address_offset, Addresses.my_x_type)
    y = read_pointer_address(Addresses.my_y_address, Addresses.my_y_address_offset, Addresses.my_y_type)
    z = read_pointer_address(Addresses.my_z_address, Addresses.my_z_address_offset, Addresses.my_z_type)
    return x, y, z


def read_target_info():
    if Addresses.attack_address_offset == [-1]:
        # Scan for ID mode
        target_id = read_memory_address(Addresses.attack_address, 0, Addresses.my_attack_type)
        if target_id and target_id > 0:
            exclude_addr = Addresses.base_address + Addresses.attack_address
            absolute_address = scan_memory_for_value(target_id, exclude_address=exclude_addr)
            if absolute_address is not None:
                # We need an offset that when added to base_address gives absolute_address
                # read_memory_address uses: base_address + address_read + offsets
                attack_address = absolute_address - Addresses.base_address
            else:
                 return 0, 0, 0, "", 0
        else:
             return 0, 0, 0, "", 0
    else:
        # Standard pointer case
        attack_address = read_memory_address(Addresses.attack_address, 0, Addresses.my_attack_type) - Addresses.base_address

    target_x = read_memory_address(attack_address, Addresses.target_x_offset, Addresses.target_x_type)
    target_y = read_memory_address(attack_address, Addresses.target_y_offset, Addresses.target_y_type)
    target_z = read_memory_address(attack_address, Addresses.target_z_offset, Addresses.target_z_type)
    target_name = read_memory_address(attack_address, Addresses.target_name_offset, Addresses.target_name_type)
    target_hp = read_memory_address(attack_address, Addresses.target_hp_offset, Addresses.target_hp_type)
    return target_x, target_y, target_z, target_name, target_hp


def scan_memory_for_value(value, exclude_address=None):
    """
    Scans the process memory for a specific 4-byte integer value.
    Iterates through all committed memory pages.
    Returns the ABSOLUTE address if found, else None.
    """
    try:
        current_address = 0
        mbi = MEMORY_BASIC_INFORMATION()
        value_bytes = struct.pack("I", value & 0xFFFFFFFF)
        
        # Determine scan limit based on architecture
        max_address = 0x7FFFFFFF if Addresses.application_architecture == 32 else 0x7FFFFFFFFFFF
        
        while current_address < max_address:
            # Query memory region
            if not c.windll.kernel32.VirtualQueryEx(Addresses.process_handle, c.c_void_p(current_address), c.byref(mbi), c.sizeof(mbi)):
                break
            
            # Check if region is COMMITTED and not NOACCESS or GUARD
            if mbi.State == 0x1000 and not (mbi.Protect & (0x100 | 0x01)):
                region_size = mbi.RegionSize
                if region_size < 100 * 1024 * 1024: # 100MB limit
                    buffer = c.create_string_buffer(region_size)
                    bytes_read = c.c_size_t()
                    
                    if c.windll.kernel32.ReadProcessMemory(Addresses.process_handle, mbi.BaseAddress, buffer, region_size, c.byref(bytes_read)):
                        data = buffer.raw[:bytes_read.value]
                        
                        search_start = 0
                        while True:
                            found_index = data.find(value_bytes, search_start)
                            if found_index == -1:
                                break
                            
                            absolute_found = current_address + found_index
                            if exclude_address is not None and absolute_found == exclude_address:
                                # Skip this one and keep looking in the same region
                                search_start = found_index + 1
                                continue
                                
                            return absolute_found
            
            # Move to the start of the next region
            current_address += mbi.RegionSize
            
        return None
        
    except Exception as e:
        print(f"Error scanning memory: {e}")


def enable_debug_privilege_pywin32():
    try:
        return memory_api.enable_debug_privilege()
        return True
    except Exception as e:
        print("Error:", e)
        return False
