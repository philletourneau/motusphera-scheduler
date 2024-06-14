import sys
import time
import threading
from animations import AnimationScheduler, SinewaveAnimation, LinearAnimation, AnimationGroupAdditive
from simulator import SimulatedSculpture, BALLS_PER_RING, STEP_SIZE_MM

# Create a global instance of SimulatedSculpture
simulatedSculpture = None

def output_positions(positions):
    # Multiply each position by 12000
    processed_positions = [pos * -12000 for pos in positions]
    processed_positions2 = SimulatedSculpture.process_positions(processed_positions, BALLS_PER_RING)
    # Update the positions of the balls in the sculpture
    simulatedSculpture.set_ball_positions(processed_positions2)
    
    print("Positions!: {}".format(processed_positions))


def main():
    global simulatedSculpture
    use_tui = "tui" in sys.argv

    if use_tui:
        import tui

    scheduler = AnimationScheduler()
    
    previous_time = time.time()

    # Define animations with start times in seconds
    mySineAnimation = SinewaveAnimation(starttime=0, max_amplitude=100, min_frequency=0.5, max_frequency=2.0)
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
        previous_time = current_time
        threading.Timer(0.25, timer_callback).start()

    # Start the timer
    timer_callback()

    # Keep the main thread alive
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
