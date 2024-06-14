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

import math

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
        self.last_positions = [0.0] * self.totalNumberOfBalls

    def updatePositions(self, currentTime: float, previousTime: float):
        self.elapsed_time += ((currentTime - previousTime) / 5)  # Adjust this factor to control speed
        #print(self.elapsed_time)

        # Calculate the current frequency using a sinusoidal function
        frequency_range = (self.max_frequency - self.min_frequency)
        frequency_offset = (self.max_frequency + self.min_frequency) / 2
        current_frequency = (currentTime - previousTime) * frequency_range

        # Introduce a frequency multiplier to make the sine wave pattern more pronounced
        frequency_multiplier = 2.0  # Adjust this value to make the sine wave more visible

        ball_index = 0

        for ring in range(self.numberOfRings):
            total_balls = self.ballsPerRing[ring]
            # Set the phase offset in degrees and convert to radians
            ring_phase_offset_degrees = ring * (360 / self.numberOfRings)
            ring_phase_offset_radians = math.radians(ring_phase_offset_degrees)

            for ball in range(total_balls):
                # Calculate the angle for the current ball
                angle = (2 * math.pi * ball) / total_balls * frequency_multiplier + ring_phase_offset_radians
                sine_value = math.sin(angle + current_frequency * self.elapsed_time)
                target_position = (self.max_amplitude / 2) * (1 + sine_value)

                self.positions[ball_index] = max(0, min(self.max_amplitude, target_position))
                self.last_positions[ball_index] = self.positions[ball_index]

                ball_index += 1

class LinearAnimation(AnimationBase):
    speed: int

    def __init__(self, starttime: int, speed: int):
        super().__init__("linear", starttime)
        self.speed = speed

    def updatePositions(self, currentTime: float, previousTime: float):
        elapsed_time = currentTime - self.starttime
        period = 10 / self.speed  # Adjust the period based on the speed

        # Calculate the position based on linear interpolation
        t = (elapsed_time % period) / period
        if t < 0.5:
            position = 2 * t  # Linearly interpolate from 0 to 1
        else:
            position = 2 * (1 - t)  # Linearly interpolate from 1 to 0

        # Set the position for all balls
        self.positions = [position for _ in range(self.totalNumberOfBalls)]



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
                modified_deltas = [int(delta * 5.8) for delta in deltas]
                print(f"FPS: {modified_deltas[:6]}")  # Print only the first 6 modified deltas


            # Update previous positions
            self.previous_positions = positions

            if self.currentAnimation.isComplete():
                self.deleteFromQueue()
                self.currentAnimation = self.animations[0] if self.animations else None

            return positions

