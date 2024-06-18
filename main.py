import sys
import time
import threading
import signal
from config import sleep_ns
from modbus_communication import send_to_modbus, cleanup, initialize_modbus, write_coils
from animation_handler import setup_scheduler
from simulation import initialize_simulation, output_positions

def main():
    use_tui = "tui" in sys.argv
    simulate = "--simulate" in sys.argv
    homing = "--homing" in sys.argv

    if use_tui:
        import tui

    scheduler = setup_scheduler()
    
    previous_time = time.time()

    # Pretty print the queued animations
    if use_tui:
        scheduler.getAnimationDetails()
    else:
        animation_details = scheduler.getAnimationDetails()
        for detail in animation_details:
            print(detail)
    
    if simulate:
        initialize_simulation()
        ctx = None  # No Modbus context in simulation mode
        desired_interval_ns = 200_000_000  # 100 milliseconds for simulation mode
    else:
        ctx = initialize_modbus()
        desired_interval_ns = 48_000_000  # 48 milliseconds for non-simulation mode

    if homing and ctx:
        # Write coils for slave IDs 1 through 3, motor IDs 0 through 3, coil 1 set to true
        for slave_id in range(1, 4):
            for motor_id in range(4):
                write_coils(ctx, slave_id, motor_id, 1, 1)
                print("Slave ID: {}, Motor ID: {}, Coil 1 set to true".format(slave_id, motor_id))
                time.sleep(0.1)
    
        time.sleep(8)

    def timer_callback():
        previous_time = time.time()
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
            else:
                intervalms = int((interval * 1000))
                send_to_modbus(ctx, positions, intervalms)
            previous_time = current_time
            sleep_ns(desired_interval_ns)

    # Start the timer
    timer_thread = threading.Thread(target=timer_callback)
    timer_thread.start()

    # Set up signal handler for graceful termination
    if ctx:
        signal.signal(signal.SIGINT, lambda signum, frame: cleanup(ctx, signum, frame))
        signal.signal(signal.SIGTERM, lambda signum, frame: cleanup(ctx, signum, frame))
    else:
        signal.signal(signal.SIGINT, lambda signum, frame: sys.exit(0))
        signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(0))

    # Keep the main thread alive
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
