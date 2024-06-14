import math
from typing import Union, Optional, List
import queue

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
        AnimationBase.__init__(self, "group", starttime)
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
        AnimationBase.__init__(self, "sine wave", starttime)
        max_amplitude = max_amplitude
    
    def updatePositions(self):
        self.positions = [math.sin(i) * self.max_amplitude for i in range(0, 360)]
        #output 0 to 1
    
class LinearAnimation(AnimationBase):
    speed: int
    def __init__(self, starttime, speed):
        AnimationBase.__init__(self, "linear", starttime)
        speed = speed
    
    def updatePositions(self):
        self.positions = [1 + 1]


class AnimationScheduler():
    animations: queue.Queue[AnimationBase] = queue.Queue()
    # Get the first animation as the current animation
    currentAnimation: Union[AnimationBase, None] = animations.queue[0] if not animations.empty() else None

    # Get the second animation as the next animation, or None if there is no second animation
    nextAnimation: Union[AnimationBase, None] = animations.queue[1] if len(animations.queue) > 1 else None

    def __init__(self):
        self.animations = []
    
    def appendToQueue(self, animation):
        self.animations.put(animation)

    def returnQueue(self):
        # loop and get names
        pass
   
    def deleteFromQueue(self):
        #delete item
        pass
    
    def getPositions(self):
        activeAnimations = list[AnimationBase]
        # loop through all animations
        for animation in self.animations:
            if animation is not None and animation.isPlaying:
                activeAnimations.append(animation)
        
        return self.positions

    def nextFrame(self, currentTime, previousTime):
        if self.currentAnimation is not None:
            self.currentAnimation.calculateNextFrame(currentTime, previousTime)
            if self.currentAnimation.isComplete():
                self.currentAnimation = self.nextAnimation

            #set the current animation
        # ok now time to translate the final 0 to 1's into 0 to 110000


#timer calls scheduler.nextFrame 

scheduler = AnimationScheduler()


mySineAnimation = SinewaveAnimation(starttime=9, max_amplitude=100)
myLinearAnimation = LinearAnimation(starttime=10, speed=100)
myGroupAnimation = AnimationGroupAdditive(starttime=99, animations=[mySineAnimation, myLinearAnimation])

#scheduler.appendToQueue(mySineAnimation)
#scheduler.appendToQueue(myLinearAnimation)
scheduler.appendToQueue(myGroupAnimation)
    