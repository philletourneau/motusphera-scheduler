import ctypes
import platform  # Add this import statement
from config import modbus_lib, MODBUS_MULTIPLIER, TIMING_SPEED_BUFFER

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

def initialize_modbus():
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
    
    return ctx

isModbusBusy = False
# Define the global counter variable
successful_runs = 0

def send_to_modbus(ctx, positions, intervalms):
    global isModbusBusy
    global successful_runs  # Declare the counter as global to modify it
    if isModbusBusy == True:
        print("Modbus is busy, skipping this frame")
        return
    isModbusBusy = True 
    #print("True")
    # Transform the positions
    processed_positions = [int(pos * MODBUS_MULTIPLIER) for pos in positions]
    print(processed_positions[:4])
    # Convert the processed positions list to a ctypes array
    positions_array = (ctypes.c_uint16 * len(processed_positions))(*processed_positions)
    #time_delta_value = 280  # Example value, replace with your actual value
    intervalms = intervalms + TIMING_SPEED_BUFFER
    modbus_lib.send_positions_over_modbus(ctx, positions_array, (intervalms))
    # Increment the counter and print the value
    successful_runs += 1
    print(f"Successful runs: {successful_runs}")
    isModbusBusy = False
    #print("False")

def cleanup(ctx, signum, frame):
    print("Cleaning up...")
    modbus_lib.close_modbus(ctx)
    sys.exit(0)
