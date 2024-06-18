from simulator import SimulatedSculpture, BALLS_PER_RING, STEP_SIZE_MM

# Create a global instance of SimulatedSculpture
simulatedSculpture = None

def initialize_simulation():
    global simulatedSculpture
    simulatedSculpture = SimulatedSculpture(ring_count=3, balls_per_ring=[50, 41, 32], step_size_mm=STEP_SIZE_MM, ball_start_y=5000)

def output_positions(positions):
    # Multiply each position by 12000
    processed_positions = [pos * -12000 for pos in positions]
    processed_positions2 = SimulatedSculpture.process_positions(processed_positions, BALLS_PER_RING)
    # Update the positions of the balls in the sculpture
    simulatedSculpture.set_ball_positions(processed_positions2)
    
    #print("Positions!: {}".format(processed_positions))
