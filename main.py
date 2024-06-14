import math
from typing import Union, Optional, List
import queue
import threading
import time

class AnimationBase():
    name: str
    starttime: int
    isPlaying: bool
    positions: List[float]
    ballsPerRing: List[int] = [50, 41, 32]
    numberOfRings: int = 3
    totalNumberOfBalls: int

    def __init__(self, name: str, starttime: int):
        self.name = name
        self.starttime = starttime
        self.isPlaying = False
        self.positions = [0] * sum(AnimationBase.ballsPerRing)
        self.totalNumberOfBalls = sum(AnimationBase.ballsPerRing)
    
    def isComplete(self) -> bool:
        pass

    def updatePositions(self):
        pass

    def calculateNextFrame(self, currentTime: float, previousTime: float):
        self.updatePositions()
    
class AnimationGroupAdditive(AnimationBase):
    animations: List[AnimationBase]

    def __init__(self, starttime: int, animations: List[AnimationBase]):
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

    def __init__(self, starttime: int, max_amplitude: int):
        super().__init__("sine wave", starttime)
        self.max_amplitude = max_amplitude
    
    def updatePositions(self):
        self.positions = [math.sin(i) * self.max_amplitude for i in range(0, 360)]
        print("updated positions in sinewave")
        #output 0 to 1
    
class LinearAnimation(AnimationBase):
    speed: int

    def __init__(self, starttime: int, speed: int):
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
        
        positions = [0] * (activeAnimations[0].totalNumberOfBalls if activeAnimations else 0)
        for animation in activeAnimations:
            for i in range(len(positions)):
                positions[i] += animation.positions[i]
        return positions
    
    def getAnimationDetails(self) -> List[str]:
        details = []
        for animation in list(self.animations.queue):
            params = ', '.join(f"{k}={v}" for k, v in animation.__dict__.items())
            details.append(f"{animation.name}({params})")
        return details

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

mySineAnimation = SinewaveAnimation(starttime=1, max_amplitude=100)
myLinearAnimation = LinearAnimation(starttime=1, speed=100)
myGroupAnimation = AnimationGroupAdditive(starttime=99, animations=[mySineAnimation, myLinearAnimation])

scheduler.appendToQueue(mySineAnimation)
#scheduler.appendToQueue(myLinearAnimation)
#scheduler.appendToQueue(myGroupAnimation)

#timer calls scheduler.nextFrame every 250ms


# Start the timer
timer_callback()