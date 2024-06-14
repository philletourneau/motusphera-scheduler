import sys
import time
import asyncio
import logging
from animations import AnimationScheduler, SinewaveAnimation, LinearAnimation, AnimationGroupAdditive
from simulator import SimulatedSculpture, BALLS_PER_RING, STEP_SIZE_MM
from modbus import async_modbus_connect, send_positions_modbus, write_coil
from constants import BALLS_PER_RING, TIMER_INTERVAL

# Create a global instance of SimulatedSculpture
simulatedSculpture = None

# Configure logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()
log.setLevel(logging.DEBUG)

def output_positions(positions):
    # Multiply each position by 12000
    processed_positions = [pos * -12000 for pos in positions]
    processed_positions2 = SimulatedSculpture.process_positions(processed_positions, BALLS_PER_RING)
    # Update the positions of the balls in the sculpture
    simulatedSculpture.set_ball_positions(processed_positions2)
    # print("Positions!: {}".format(processed_positions))

async def main():
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

    client = None
    try:
        client = await async_modbus_connect()
        # coil_address = 1  # Example coil address
        # coil_value = True  # Example coil value (True for ON, False for OFF)
        # for slave_id in [1, 2]:  # Slave IDs 1 and 2
        #     for motor_id in range(4):  # Motor IDs 0 to 3
        #         await write_coil(client, slave_id, motor_id, coil_address, coil_value)

        await asyncio.sleep(15)

        async def timer_callback():
            nonlocal previous_time
            current_time = time.time()
            positions = scheduler.nextFrame(current_time, previous_time)
            output_positions(positions)
            await send_positions_modbus(client, positions)
            previous_time = current_time
            await asyncio.sleep(TIMER_INTERVAL)
            await timer_callback()

        # Start the timer
        await timer_callback()

        # Keep the main thread alive
        while True:
            await asyncio.sleep(1)
    finally:
        # Ensure the client is closed properly
        if client and client.connected:
            await client.close()
        logging.debug("Modbus client closed")

if __name__ == "__main__":
    asyncio.run(main())
