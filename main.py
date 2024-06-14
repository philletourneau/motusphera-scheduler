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

# Load the shared library
modbus_lib = ctypes.CDLL('./libmodbus_utils.dylib')

# Define the argument and return types of the functions you will use
modbus_lib.initialize_modbus.argtypes = [ctypes.c_char_p, ctypes.c_int]
modbus_lib.initialize_modbus.restype = ctypes.c_void_p

modbus_lib.send_positions_over_modbus.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint16), ctypes.c_uint16]
modbus_lib.send_positions_over_modbus.restype = None

modbus_lib.close_modbus.argtypes = [ctypes.c_void_p]
modbus_lib.close_modbus.restype = None

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

    if use_tui:
        import tui

    scheduler = AnimationScheduler()
    
    previous_time = time.time()

    # Define animations with start times in seconds
    mySineAnimation = SinewaveAnimation(starttime=40, max_amplitude=0.5, min_frequency=0.1, max_frequency=3.0)
    myLinearAnimation = LinearAnimation(starttime=0, speed=0.5)
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

    def timer_callback():
        current_time = time.time()
        nonlocal previous_time
        interval = current_time - previous_time
        print(f"Interval between timer callbacks: {interval:.6f} seconds")
        positions = scheduler.nextFrame(current_time, previous_time)
        if positions is None:
            print("Error: positions is None")
            return
        if simulate:
            output_positions(positions)
        intervalms = int((interval * 1000))
        send_to_modbus(positions, intervalms)
        # Print only the first 6 positions
        #print("Positions: {}".format(positions[:6]))
        previous_time = current_time
        threading.Timer(0.04, timer_callback).start()

    # Start the timer
    timer_callback()

    # Set up signal handler for graceful termination
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # Keep the main thread alive
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
