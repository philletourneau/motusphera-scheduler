import sys
import time
import threading
from animations import AnimationScheduler, SinewaveAnimation, LinearAnimation, AnimationGroupAdditive

def output_positions(positions):
    # Do something with the positions
    print("Current positions:", positions)
def main():
    if "tui" in sys.argv:
        import tui
    else:
        scheduler = AnimationScheduler()
        
        previous_time = time.time()

        # Define animations with start times in seconds
        mySineAnimation = SinewaveAnimation(starttime=1, max_amplitude=100)
        myLinearAnimation = LinearAnimation(starttime=2, speed=100)
        myGroupAnimation = AnimationGroupAdditive(starttime=5, animations=[mySineAnimation, myLinearAnimation])

        # Append animations to scheduler
        scheduler.appendToQueue(mySineAnimation)
        scheduler.appendToQueue(myLinearAnimation)
        scheduler.appendToQueue(myGroupAnimation)

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
