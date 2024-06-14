import math
import queue
import time
from typing import List, Optional

# Initialize program start time
program_start_time = time.time()

class AnimationBase:
    name: str
    starttime: int
    isPlaying: bool
    positions: List[float]
    ballsPerRing: List[int]
    numberOfRings: int
    totalNumberOfBalls: int

    def __init__(self, name: str, starttime: int, ballsPerRing: List[int] = [50, 41, 32]):
        self.name = name
        self.starttime = starttime
        self.isPlaying = False
        self.ballsPerRing = ballsPerRing
        self.numberOfRings = len(ballsPerRing)
        self.positions = [0] * sum(self.ballsPerRing)
        self.totalNumberOfBalls = sum(self.ballsPerRing)
    
    def isComplete(self) -> bool:
        return False

    def updatePositions(self, currentTime: float, previousTime: float):
        pass

    def calculateNextFrame(self, currentTime: float, previousTime: float):
        self.updatePositions(currentTime, previousTime)

class AnimationGroupAdditive(AnimationBase):
    animations: List[AnimationBase]

    def __init__(self, starttime: int, animations: List[AnimationBase]):
        super().__init__("combo", starttime)
        self.animations = animations
    
    def updatePositions(self, currentTime: float, previousTime: float):
        self.positions = [0] * self.totalNumberOfBalls
        
        for animation in self.animations:
            animation.updatePositions(currentTime, previousTime)
            for i in range(len(self.positions)):
                self.positions[i] += animation.positions[i]
        # Normalize the positions to ensure they are between 0 and 1
        max_position = max(self.positions) if self.positions else 1
        if max_position != 0:
            self.positions = [p / max_position for p in self.positions]

class SinewaveAnimation(AnimationBase):
    max_amplitude: int
    min_frequency: float
    max_frequency: float
    elapsed_time: float

    def __init__(self, starttime: int, max_amplitude: int, min_frequency: float, max_frequency: float):
        super().__init__("sine wave", starttime)
        self.max_amplitude = max_amplitude
        self.min_frequency = min_frequency
        self.max_frequency = max_frequency
        self.elapsed_time = 0.0
    
    def updatePositions(self, currentTime: float, deltaTime: float):
        self.elapsed_time += deltaTime
        
        # Slow down the animation by scaling down the elapsed time
        slow_factor = 0.1  # Adjust this factor to slow down the animation (0.5 means half speed)
        scaled_elapsed_time = self.elapsed_time * slow_factor
        
        # Calculate the current frequency using a sinusoidal function
        frequency_range = (self.max_frequency - self.min_frequency) / 2
        frequency_offset = (self.max_frequency + self.min_frequency) / 2
        current_frequency = frequency_range * math.sin(scaled_elapsed_time) + frequency_offset
        
        self.positions = [(math.sin(math.radians(i * current_frequency)) * self.max_amplitude + self.max_amplitude) / (2 * self.max_amplitude) for i in range(360)]

class LinearAnimation(AnimationBase):
    speed: int

    def __init__(self, starttime: int, speed: int):
        super().__init__("linear", starttime)
        self.speed = speed
    
    def updatePositions(self, currentTime: float, previousTime: float):
        self.positions = [i / self.totalNumberOfBalls for i in range(self.totalNumberOfBalls)]

class AnimationScheduler:
    def __init__(self):
        self.animations = queue.Queue()
        self.currentAnimation: Optional[AnimationBase] = None
        self.nextAnimation: Optional[AnimationBase] = None
    
    def appendToQueue(self, animation: AnimationBase):
        self.animations.put(animation)
        if not self.currentAnimation:
            self.currentAnimation = self.animations.get()
            self.nextAnimation = self.animations.queue[0] if not self.animations.empty() else None

    def returnQueue(self) -> List[str]:
        return [animation.name for animation in list(self.animations.queue)]
   
    def deleteFromQueue(self):
        if not self.animations.empty():
            self.animations.get()
            self.currentAnimation = self.animations.queue[0] if not self.animations.empty() else None
    
    ### I don't know if I still need this?  ###
    # keeping it for the terminal UI for now
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
    
    def getAnimationDetails(self):
            details = []

            # Include current animation if it exists
            if hasattr(self, 'current_animation') and self.current_animation:
                current_animation = self.current_animation
                params = '\n'.join(f"  {k}: {v}" for k, v in current_animation.__dict__.items() if k != 'positions')
                details.append(f"[Current] {current_animation.name}:\n{params}")

            for animation in self.animations.queue:
                params = '\n'.join(f"  {k}: {v}" for k, v in animation.__dict__.items() if k != 'positions')
                details.append(f"{animation.name}:\n{params}")
            return details

    def nextFrame(self, currentTime, previousTime):
        # Check if currentAnimation should start
        if self.currentAnimation and not self.currentAnimation.isPlaying:
            elapsed_time = currentTime - program_start_time
            if elapsed_time >= self.currentAnimation.starttime:
                self.currentAnimation.isPlaying = True

        if self.currentAnimation and self.currentAnimation.isPlaying:
            self.currentAnimation.calculateNextFrame(currentTime, previousTime)
            #positions_str = ', '.join(f"{pos:.2f}" for pos in self.currentAnimation.positions)
            if self.currentAnimation.isComplete():
                self.deleteFromQueue()
                self.currentAnimation = self.animations.queue[0] if not self.animations.empty() else None
            
            return self.currentAnimation.positions

