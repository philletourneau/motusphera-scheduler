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


class SineWaveAnimation(AnimationBase):
    speed: int
    min_value: float
    max_value: float
    frequency_multiplier: float
    wavelength_modifier: float

    def __init__(self, starttime: int, speed: int, min_value: float = 0.1, max_value: float = 0.4, frequency_multiplier: float = 1.0, wavelength_modifier: float = 1.0):
        super().__init__("snake", starttime)
        self.speed = speed
        self.min_value = min_value
        self.max_value = max_value
        self.frequency_multiplier = frequency_multiplier
        self.wavelength_modifier = wavelength_modifier

    def updatePositions(self, currentTime: float, previousTime: float):
        elapsed_time = currentTime - self.starttime
        #print("elapsed time: ", elapsed_time)

        ball_index = 0
        for ring in range(self.numberOfRings):
            total_balls = self.ballsPerRing[ring]
            for ball in range(total_balls):
                # Each ball in the ring will have a phase shift based on its index, frequency multiplier, and wavelength modifier
                phase_shift = self.frequency_multiplier * (2 * math.pi * ball) / (total_balls * self.wavelength_modifier)
                sine_value = math.sin((elapsed_time * self.speed) + phase_shift)
                
                # Scale the position to the desired range
                position = self.min_value + (self.max_value - self.min_value) * (0.5 * (1 + sine_value))
                
                self.positions[ball_index] = position
                ball_index += 1

        #print(self.positions[:3])  # Print only the first 3 positions for debugging

class LinearAnimation(AnimationBase):
    speed: int
    min_value: float
    max_value: float

    def __init__(self, starttime: int, speed: int, min_value: float = 0.1, max_value: float = 0.4):
        super().__init__("linear", starttime)
        self.speed = speed
        self.min_value = min_value
        self.max_value = max_value

    def triangular_wave(self, t: float) -> float:
        return 2 * abs(t - math.floor(t + 0.5))

    def updatePositions(self, currentTime: float, previousTime: float):
        elapsed_time = currentTime - self.starttime
        #print("elapsed time: ", elapsed_time)
        period = 10 / self.speed  # Adjust the period based on the speed

        # Calculate the position based on linear interpolation
        t = (elapsed_time % period) / period

        # Apply the triangular wave function
        wave_t = self.triangular_wave(t)

        # Scale the position to the desired range
        position = self.min_value + (self.max_value - self.min_value) * wave_t

        # Set the position for all balls
        self.positions = [position for _ in range(self.totalNumberOfBalls)]

        #print(self.positions)


class AnimationScheduler:
    def __init__(self):
        self.animations = queue.Queue()
        self.currentAnimation: Optional[AnimationBase] = None
        self.nextAnimation: Optional[AnimationBase] = None
        self.previous_positions = None  # Variable to store previous positions
    
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
            positions = self.currentAnimation.positions

            # Calculate and print deltas
            if self.previous_positions is not None:
                deltas = [abs(round((current - previous)*12000)) for current, previous in zip(positions, self.previous_positions)]
                #print(f"Deltas: {deltas[:6]}")  # Print only the first 6 deltas
                #multiply each delta by 5.8
                #print(f"Positions: {positions[0]*12000}")  # Print only the first 6 positions
                modified_deltas = [int(delta * 5.8) for delta in deltas]
                #print(f"FPS: {modified_deltas[:6]}")  # Print only the first 6 modified deltas


            # Update previous positions
            self.previous_positions = positions

            if self.currentAnimation.isComplete():
                self.deleteFromQueue()
                self.currentAnimation = self.animations[0] if self.animations else None

            #print(positions)
            return positions

