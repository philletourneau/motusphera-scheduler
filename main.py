import sys
import time
import threading
import ctypes
import platform
import signal
import numpy as np
from animations import AnimationScheduler, SinewaveAnimation, LinearAnimation, AnimationGroupAdditive
from simulator import SimulatedSculpture, BALLS_PER_RING, STEP_SIZE_MM

# Define the MODBUS_MULTIPLIER
MODBUS_MULTIPLIER = 12000
TIMING_SPEED_BUFFER = 40

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

# Define the argument and return types of the functions you will use
modbus_lib.initialize_modbus.argtypes = [ctypes.c_char_p, ctypes.c_int]
modbus_lib.initialize_modbus.restype = ctypes.c_void_p

modbus_lib.write_coils.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_uint8), ctypes.c_int]
modbus_lib.write_coils.restype = None

modbus_lib.send_positions_over_modbus.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint16), ctypes.c_uint16]
modbus_lib.send_positions_over_modbus.restype = None

modbus_lib.close_modbus.argtypes = [ctypes.c_void_p]
modbus_lib.close_modbus.restype = None

def write_coils(ctx, slave_id, motor_id, start_address, coil_value):
    coils = (ctypes.c_uint8 * 1)(coil_value)
    modbus_lib.write_coils(ctx, slave_id, motor_id, start_address, coils, 1)

# Determine the port based on the operating system
if platform.system() == 'Darwin':  # MacOS
    port = '/dev/tty.usbserial-AC0134TM'
else:
    port = '/dev/ttyUSB0'

# Initialize the Modbus connection using the port variable
device = port.encode('utf-8')  # Convert the port string to bytes
baud_rate = 460800
ctx = modbus_lib.initialize_modbus(device, baud_rate)

if not ctx:
    raise Exception("Failed to initialize Modbus connection")

def send_to_modbus(positions, intervalms):
    # Transform the positions
    processed_positions = [int(pos * MODBUS_MULTIPLIER) for pos in positions]
    
    # Convert the processed positions list to a ctypes array
    positions_array = (ctypes.c_uint16 * len(processed_positions))(*processed_positions)
    #time_delta_value = 280  # Example value, replace with your actual value
    intervalms = intervalms + TIMING_SPEED_BUFFER
    modbus_lib.send_positions_over_modbus(ctx, positions_array, intervalms)

# Create a global instance of SimulatedSculpture
simulatedSculpture = None

def output_positions(positions):
    # Multiply each position by 12000
    processed_positions = [pos * -12000 for pos in positions]
    processed_positions2 = SimulatedSculpture.process_positions(processed_positions, BALLS_PER_RING)
    # Update the positions of the balls in the sculpture
    simulatedSculpture.set_ball_positions(processed_positions2)
    
    #print("Positions!: {}".format(processed_positions))

def cleanup(signum, frame):
    print("Cleaning up...")
    modbus_lib.close_modbus(ctx)
    sys.exit(0)

def main():
    global simulatedSculpture
    use_tui = "tui" in sys.argv
    simulate = "--simulate" in sys.argv
    homing = "--homing" in sys.argv

    if use_tui:
        import tui

    scheduler = AnimationScheduler()
    
    previous_time = time.time()

    # Define animations with start times in seconds
    mySineAnimation = SinewaveAnimation(starttime=40, max_amplitude=0.5, min_frequency=0.1, max_frequency=3.0)
    myLinearAnimation = LinearAnimation(starttime=0, speed=0.2)
    myGroupAnimation = AnimationGroupAdditive(starttime=50, animations=[mySineAnimation, myLinearAnimation])

    # Append animations to scheduler
    scheduler.appendToQueue(myLinearAnimation)
    scheduler.appendToQueue(myGroupAnimation)
    scheduler.appendToQueue(mySineAnimation)

    # Pretty print the queued animations
    if use_tui:
        scheduler.getAnimationDetails()
    else:
        animation_details = scheduler.getAnimationDetails()
        for detail in animation_details:
            print(detail)
    
    if simulate:
        # Initialize the SimulatedSculpture
        simulatedSculpture = SimulatedSculpture(ring_count=3, balls_per_ring=[50, 41, 32], step_size_mm=STEP_SIZE_MM, ball_start_y=5000)

    if homing:
        # Write coils for slave IDs 1 through 3, motor IDs 0 through 3, coil 1 set to true
        for slave_id in range(1, 4):
            for motor_id in range(4):
                write_coils(ctx, slave_id, motor_id, 1, 1)
                print("Slave ID: {}, Motor ID: {}, Coil 1 set to true".format(slave_id, motor_id))
                time.sleep(0.1)
    
        time.sleep(8)

    def timer_callback():
        previous_time = time.time()
        desired_interval_ns = 80_000_000  # Desired interval in nanoseconds (0.08 seconds)
        while True:
            current_time = time.time()
            interval = current_time - previous_time
            interval_ms = interval * 1000
            print(f"Interval between callbacks: {interval_ms:.0f} milliseconds")
            positions = scheduler.nextFrame(current_time, previous_time)
            if positions is None:
                print("Error: positions is None")
                continue
            if simulate:
                output_positions(positions)
            intervalms = int((interval * 1000))
            send_to_modbus(positions, intervalms)
            previous_time = current_time
            sleep_ns(desired_interval_ns)

    # # Start the timer
    # timer_callback()
    # Start the timer
    timer_thread = threading.Thread(target=timer_callback)
    timer_thread.start()

    # Set up signal handler for graceful termination
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # Keep the main thread alive
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
