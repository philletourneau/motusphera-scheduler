import platform
import ctypes

# Define the MODBUS_MULTIPLIER
MODBUS_MULTIPLIER = 12000
TIMING_SPEED_BUFFER = 10

# Detect platform and set the shared library path
if platform.system() == 'Darwin':  # macOS
    lib_path = './prebuilt/modbus_utils/darwin/libmodbus_utils.dylib'
    # Define the Mach kernel functions for macOS
    libc = ctypes.CDLL('/usr/lib/libSystem.dylib')
    mach_absolute_time = libc.mach_absolute_time
    mach_absolute_time.restype = ctypes.c_uint64

    class mach_timebase_info_data_t(ctypes.Structure):
        _fields_ = [("numer", ctypes.c_uint32), ("denom", ctypes.c_uint32)]

    mach_timebase_info = libc.mach_timebase_info
    mach_timebase_info.argtypes = [ctypes.POINTER(mach_timebase_info_data_t)]
    mach_timebase_info.restype = None

    timebase_info = mach_timebase_info_data_t()
    mach_timebase_info(ctypes.byref(timebase_info))

    def sleep_ns(nanos):
        start = mach_absolute_time()
        end = start + nanos * timebase_info.denom // timebase_info.numer
        while mach_absolute_time() < end:
            pass
else:  # Linux
    lib_path = './prebuilt/modbus_utils/linux/libmodbus_utils.so'

    # Define clock_nanosleep for Linux
    libc = ctypes.CDLL('libc.so.6')
    CLOCK_MONOTONIC = 1
    TIMER_ABSTIME = 1

    class timespec(ctypes.Structure):
        _fields_ = [("tv_sec", ctypes.c_long), ("tv_nsec", ctypes.c_long)]

    def sleep_ns(nanos):
        ts = timespec()
        libc.clock_gettime(CLOCK_MONOTONIC, ctypes.byref(ts))
        ts.tv_sec += nanos // 1_000_000_000
        ts.tv_nsec += nanos % 1_000_000_000
        if ts.tv_nsec >= 1_000_000_000:
            ts.tv_sec += 1
            ts.tv_nsec -= 1_000_000_000
        libc.clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, ctypes.byref(ts), None)

# Load the shared library
modbus_lib = ctypes.CDLL(lib_path)
