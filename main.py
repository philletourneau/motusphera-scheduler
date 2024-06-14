import sys
import time
import threading
from animations import AnimationScheduler, SinewaveAnimation, LinearAnimation, AnimationGroupAdditive

def output_positions(positions):
    # Do something with the positions
    print("Current positions:", positions)

def main():
    use_tui = "tui" in sys.argv

    if use_tui:
        import tui

    scheduler = AnimationScheduler()
    
    previous_time = time.time()

    # Define animations with start times in seconds
    mySineAnimation = SinewaveAnimation(starttime=1, max_amplitude=100, min_frequency=0.5, max_frequency=2.0)
    myLinearAnimation = LinearAnimation(starttime=42, speed=100)
    myGroupAnimation = AnimationGroupAdditive(starttime=50, animations=[mySineAnimation, myLinearAnimation])
    myLinearAnimation = LinearAnimation(starttime=20, speed=90)

    # Append animations to scheduler
    scheduler.appendToQueue(mySineAnimation)
    scheduler.appendToQueue(myLinearAnimation)
    scheduler.appendToQueue(myGroupAnimation)

    # Pretty print the queued animations
    if use_tui:
        scheduler.getAnimationDetails(use_rich=True)
    else:
        animation_details = scheduler.getAnimationDetails()
        for detail in animation_details:
            print(detail)

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
