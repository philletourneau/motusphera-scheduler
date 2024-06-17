from vpython import sphere, vector, curve, color, canvas
import math
import time

# Constants related to the sculpture
STEP_SIZE_MM = 20
MAX_DISTANCE_STEPS = 12000.0
MAX_DISTANCE_MM = MAX_DISTANCE_STEPS / STEP_SIZE_MM
BASE_RADIUS = 1219.2
GAP_BETWEEN_RINGS = 228.6
MAX_DISTANCE_STEPS = 11000.0
MAX_BALL_VELOCITY = 2800.0
BALL_RADIUS_MM = 40
BALL_SPACING_MM = 240.0
STEP_SIZE_MM = (5.0 * 180.0) / MAX_DISTANCE_STEPS
RING_COUNT = 3
BALLS_PER_RING = [50, 41, 32]  # Number of balls in each ring
Y_OFFSET = 100

class SimulatedSculpture:
    def __init__(self, ring_count, balls_per_ring, ball_start_y, step_size_mm):
        self.ring_count = ring_count
        self.balls_per_ring = balls_per_ring
        self.ball_start_y = ball_start_y
        self.step_size_mm = step_size_mm
        self.last_frame_time = None
        self.last_positions = []

        overall_height = STEP_SIZE_MM * MAX_DISTANCE_STEPS + 500

        self.resize_canvas(overall_height)
        self.make_bounding_box(overall_height)
        self.make_balls(overall_height)

        self.last_frame_time = None

    def resize_canvas(self, overall_height):
        current_canvas = canvas.get_selected()
        current_canvas.width = overall_height / 1.4
        current_canvas.height = overall_height / 1.5

    def make_bounding_box(self, overall_height):
        margin = BALL_RADIUS_MM * 18
        box_height = overall_height + margin

        uppermost = box_height / 1.6
        lowermost = -1.0 * uppermost

        radius = 2.0

        # Top square
        curve(
            pos=[
                vector(uppermost, uppermost, uppermost),
                vector(lowermost, uppermost, uppermost),
                vector(lowermost, uppermost, lowermost),
                vector(uppermost, uppermost, lowermost),
                vector(uppermost, uppermost, uppermost)
            ],
            radius=radius
        )

        # Bottom square
        curve(
            pos=[
                vector(uppermost, lowermost, uppermost),
                vector(lowermost, lowermost, uppermost),
                vector(lowermost, lowermost, lowermost),
                vector(uppermost, lowermost, lowermost),
                vector(uppermost, lowermost, uppermost)
            ],
            radius=radius
        )

        # Sides
        curve(pos=[vector(uppermost, uppermost, uppermost), vector(uppermost, lowermost, uppermost)], radius=radius)
        curve(pos=[vector(uppermost, uppermost, lowermost), vector(uppermost, lowermost, lowermost)], radius=radius)
        curve(pos=[vector(lowermost, uppermost, lowermost), vector(lowermost, lowermost, lowermost)], radius=radius)
        curve(pos=[vector(lowermost, uppermost, uppermost), vector(lowermost, lowermost, uppermost)], radius=radius)

    def make_balls(self, overall_height):
        self.ball_start_y = overall_height
        self.balls = []

        for ring_index in range(self.ring_count):
            ball_row = []
            ring_radius = BASE_RADIUS - (ring_index * GAP_BETWEEN_RINGS)
            num_balls = self.balls_per_ring[ring_index]

            for ball_index in range(num_balls):
                angle = (2 * math.pi / num_balls) * ball_index
                ball_x = ring_radius * math.cos(angle)
                ball_z = ring_radius * math.sin(angle)
                ball = sphere(pos=vector(ball_x, self.ball_start_y, ball_z), radius=BALL_RADIUS_MM, color=color.white)
                ball_row.append(ball)
            self.balls.append(ball_row)

    @staticmethod
    def process_positions(flat_positions, balls_per_ring):
        frame = []
        index = 0
        for num_balls in balls_per_ring:
            ring_positions = flat_positions[index:index + num_balls]
            frame.append(ring_positions)
            index += num_balls
        return frame

    def get_ball_positions(self):
        frame = []
        for row_index, ball_row in enumerate(self.balls):
            frame_row = []
            for column_index, ball in enumerate(ball_row):
                position = (ball.pos.y - self.ball_start_y) / self.step_size_mm
                frame_row.append(position)
            frame.append(frame_row)
        return frame

    def set_ball_positions(self, frame):
        last_positions = self.get_ball_positions()

        now = time.monotonic()
        time_since_last_frame = None
        if self.last_frame_time is not None:
            time_since_last_frame = now - self.last_frame_time
        self.last_frame_time = now

        # Debug print to understand the structure of frame
        #print("Frame structure:", frame)

        for ring_index, ring in enumerate(frame):
            for ball_index, frame_position in enumerate(ring):
                if frame_position > 0.0:
                    print(f'WARNING: Ball was commanded to move above the top of the sculpture! {frame_position}')
                elif frame_position > MAX_DISTANCE_STEPS:
                    print(f'WARNING: Ball was commanded to move beyond the range of the sculpture! {frame_position} vs {MAX_DISTANCE_STEPS}')

                last_position = last_positions[ring_index][ball_index]
                if time_since_last_frame is not None:
                    velocity = abs(frame_position - last_position) / time_since_last_frame
                    if velocity > MAX_BALL_VELOCITY:
                        print(f'WARNING: Faster than max velocity! ({velocity} vs {MAX_BALL_VELOCITY} steps/s)')
                    #     # Clamp the velocity
                    #     if frame_position > last_position:
                    #         frame_position = last_position + MAX_BALL_VELOCITY * time_since_last_frame
                    #     else:
                    #         frame_position = last_position - MAX_BALL_VELOCITY * time_since_last_frame

                ball = self.balls[ring_index][ball_index]
                position = self.ball_start_y + (frame_position * STEP_SIZE_MM)
                position = int(position)
                ball.pos = vector(ball.pos.x, position, ball.pos.z)

        # Update the last positions after setting them
        self.last_positions = frame
