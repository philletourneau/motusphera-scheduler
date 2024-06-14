import math
from typing import Union, Optional, List
import queue
import threading
import time

class AnimationBase():
    name: str
    starttime: int
    isPlaying: bool
    positions: list[float]
    ballsPerRing: List[int] = [50, 41, 32]
    numberOfRings: int = 3
    totalNumberOfBalls: int

    def __init__(self, name, starttime):
        self.name = name
        self.starttime = starttime
        self.isPlaying = False
        self.positions = [0] * sum(AnimationBase.ballsPerRing)
        self.totalNumberOfBalls = sum(AnimationBase.ballsPerRing)
    
    def isComplete(self):
        pass

    def updatePositions(self):
        pass
    def calculateNextFrame(self, currentTime, previousTime):
        self.updatePositions()
    
class AnimationGroupAdditive(AnimationBase):
    animations: list[AnimationBase]
    def __init__(self, starttime, animations):
        super().__init__("group", starttime)
        self.animations = animations
    
    def updatePositions(self):
        #iterate through positions list and reset them to 0
        self.positions.clear()
        
        for animation in self.animations:
            animation.updatePositions()
            self.positions += animation.positions
        

class SinewaveAnimation(AnimationBase):
    max_amplitude: int
    def __init__(self, starttime, max_amplitude):
        super().__init__("sine wave", starttime)
        self.max_amplitude = max_amplitude
    
    def updatePositions(self):
        self.positions = [math.sin(i) * self.max_amplitude for i in range(0, 360)]
        #output 0 to 1
    
class LinearAnimation(AnimationBase):
    speed: int
    def __init__(self, starttime, speed):
        super().__init__("linear", starttime)
        self.speed = speed
    
    def updatePositions(self):
        self.positions = [1 + 1]


class AnimationScheduler():
    def __init__(self):
        self.animations = queue.Queue()
        self.currentAnimation: Optional[AnimationBase] = None
        self.nextAnimation: Optional[AnimationBase] = None
    
    def appendToQueue(self, animation):
        self.animations.put(animation)

    def returnQueue(self) -> List[str]:
        return [animation.name for animation in list(self.animations.queue)]
   
    def deleteFromQueue(self):
        if not self.animations.empty():
            self.animations.get()
            self.currentAnimation = self.animations.queue[0] if not self.animations.empty() else None
    
    def getPositions(self) -> List[float]:
        activeAnimations = []
        for animation in list(self.animations.queue):
            if animation.isPlaying:
                activeAnimations.append(animation)
        
        return self.positions

    def nextFrame(self, currentTime, previousTime):
        if self.currentAnimation is not None:
            self.currentAnimation.calculateNextFrame(currentTime, previousTime)
            if self.currentAnimation.isComplete():
                self.currentAnimation = self.nextAnimation

            #set the current animation
        # ok now time to translate the final 0 to 1's into 0 to 110000

def timer_callback():
    current_time = time.time()
    global previous_time
    scheduler.nextFrame(current_time, previous_time)
    print("Positions: ", scheduler.getPositions())
    #print("Queue: ", scheduler.returnQueue())
    print("Details: ", scheduler.getAnimationDetails())
    previous_time = current_time
    threading.Timer(0.25, timer_callback).start()

previous_time = time.time()
scheduler = AnimationScheduler()


mySineAnimation = SinewaveAnimation(starttime=9, max_amplitude=100)
myLinearAnimation = LinearAnimation(starttime=10, speed=100)
myGroupAnimation = AnimationGroupAdditive(starttime=99, animations=[mySineAnimation, myLinearAnimation])

scheduler.appendToQueue(mySineAnimation)
#scheduler.appendToQueue(myLinearAnimation)
#scheduler.appendToQueue(myGroupAnimation)

#timer calls scheduler.nextFrame every 250ms


# Start the timer
timer_callback()