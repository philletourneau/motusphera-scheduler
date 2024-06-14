import sys
import time
import threading
import ctypes
import numpy as np
from animations import AnimationScheduler, SinewaveAnimation, LinearAnimation, AnimationGroupAdditive
from simulator import SimulatedSculpture, BALLS_PER_RING, STEP_SIZE_MM

# Load the shared library
modbus_lib = ctypes.CDLL('./libmodbus_utils.dylib')

# Define the argument and return types of the functions you will use
modbus_lib.initialize_modbus.argtypes = [ctypes.c_char_p, ctypes.c_int]
modbus_lib.initialize_modbus.restype = ctypes.c_void_p

modbus_lib.send_positions_over_modbus.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint16), ctypes.c_uint16]
modbus_lib.send_positions_over_modbus.restype = None

modbus_lib.close_modbus.argtypes = [ctypes.c_void_p]
modbus_lib.close_modbus.restype = None

# Initialize the Modbus connection
device = b'/dev/ttyUSB0'  # Replace with your actual device
baud_rate = 9600
ctx = modbus_lib.initialize_modbus(device, baud_rate)

if not ctx:
    raise Exception("Failed to initialize Modbus connection")

# Create a global instance of SimulatedSculpture
simulatedSculpture = None

def output_positions(positions):
    # Multiply each position by 12000
    processed_positions = [pos * -12000 for pos in positions]
    processed_positions2 = SimulatedSculpture.process_positions(processed_positions, BALLS_PER_RING)
    # Update the positions of the balls in the sculpture
    simulatedSculpture.set_ball_positions(processed_positions2)
    
    #print("Positions!: {}".format(processed_positions))


def main():
    global simulatedSculpture
    use_tui = "tui" in sys.argv

    if use_tui:
        import tui

    scheduler = AnimationScheduler()
    
    previous_time = time.time()

    # Define animations with start times in seconds
    mySineAnimation = SinewaveAnimation(starttime=0, max_amplitude=0.5, min_frequency=0.1, max_frequency=3.0)
    myLinearAnimation = LinearAnimation(starttime=42, speed=100)
    myGroupAnimation = AnimationGroupAdditive(starttime=50, animations=[mySineAnimation, myLinearAnimation])
    myLinearAnimation = LinearAnimation(starttime=20, speed=90)

    # Append animations to scheduler
    scheduler.appendToQueue(mySineAnimation)
    scheduler.appendToQueue(myLinearAnimation)
    scheduler.appendToQueue(myGroupAnimation)

    # Pretty print the queued animations
    if use_tui:
        scheduler.getAnimationDetails()
    else:
        animation_details = scheduler.getAnimationDetails()
        for detail in animation_details:
            print(detail)
    
    # Initialize the SimulatedSculpture
    simulatedSculpture = SimulatedSculpture(ring_count=3, balls_per_ring=[50, 41, 32], step_size_mm=STEP_SIZE_MM, ball_start_y=5000)

    def timer_callback():
        current_time = time.time()
        nonlocal previous_time
        positions = scheduler.nextFrame(current_time, previous_time)
        output_positions(positions)
        send_to_modbus(positions)
        previous_time = current_time
        threading.Timer(0.25, timer_callback).start()

    # Start the timer
    timer_callback()

    # Keep the main thread alive
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
