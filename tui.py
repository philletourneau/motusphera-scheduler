import curses
import threading
import time
from animations import AnimationScheduler, SinewaveAnimation, LinearAnimation, AnimationGroupAdditive

scheduler = AnimationScheduler()
positions = []
positions_lock = threading.Lock()

def update_display(stdscr):
    global positions

    # Initialize curses and set up color pairs
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)

    # Clear screen
    stdscr.clear()

    # Create windows for different sections
    height, width = stdscr.getmaxyx()
    positions_win = curses.newwin(height // 2, width, 0, 0)
    queue_win = curses.newwin(height // 2, width, height // 2, 0)

    while True:
        # Update positions window
        positions_win.clear()
        positions_win.bkgd(curses.color_pair(1))
        positions_win.box()
        positions_win.addstr(0, 2, "Animation Positions", curses.color_pair(1) | curses.A_BOLD)
        
        with positions_lock:
            if positions is not None:
                for idx, pos in enumerate(positions):
                    try:
                        if isinstance(pos, (int, float)):
                            positions_win.addstr(idx + 1, 2, f"Position {idx}: {pos:.4f}"[:width-4])
                        else:
                            positions_win.addstr(idx + 1, 2, f"Position {idx}: {pos}"[:width-4])
                    except curses.error:
                        pass  # Ignore errors caused by writing out of bounds
        
        positions_win.refresh()

        # Update queue window
        queue_win.clear()
        queue_win.bkgd(curses.color_pair(2))
        queue_win.box()
        queue_win.addstr(0, 2, "Animation Queue", curses.color_pair(2) | curses.A_BOLD)
        details = scheduler.getAnimationDetails()
        for idx, detail in enumerate(details):
            queue_win.addstr(idx + 1, 2, detail)
        queue_win.refresh()

        # Delay to prevent flickering
        time.sleep(0.25)

def output_positions(new_positions):
    global positions
    with positions_lock:
        positions = new_positions if new_positions is not None else []

def curses_thread():
    curses.wrapper(update_display)

def timer_callback():
    current_time = time.time()
    global previous_time
    new_positions = scheduler.nextFrame(current_time, previous_time)
    output_positions(new_positions)
    previous_time = current_time
    threading.Timer(0.25, timer_callback).start()

previous_time = time.time()

# Define animations with start times in seconds
mySineAnimation = SinewaveAnimation(starttime=1, max_amplitude=100)
myLinearAnimation = LinearAnimation(starttime=2, speed=100)
myGroupAnimation = AnimationGroupAdditive(starttime=5, animations=[mySineAnimation, myLinearAnimation])

# Append animations to scheduler
scheduler.appendToQueue(mySineAnimation)
scheduler.appendToQueue(myLinearAnimation)
scheduler.appendToQueue(myGroupAnimation)

# Start the timer
timer_callback()

# Start the curses interface in a separate thread
tui_thread = threading.Thread(target=curses_thread)
tui_thread.daemon = True
tui_thread.start()

# Keep the main thread alive
while True:
    time.sleep(1)
