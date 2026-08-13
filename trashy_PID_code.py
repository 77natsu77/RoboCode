from sbot import motors, utils, arduino, AnalogPin, vision
from enum import Enum
import time
import collections

# Utility functions
def set_motors(left: float,right: float):
    motors.set_power(0,left)
    motors.set_power(1,right)


def set_state(state):
    if state == "forward":
        set_motors(0.2,0.2)
    elif state == "left":
        set_motors(0.2,0.3)
    elif state == "right":
        set_motors(0.3,0.2)

def find_target(markerlist, target):
    for marker in markerlist:
        if marker.id == target:
            return marker
    return None


#Task 2 part 1
def Task_2_part_2():
    motors.set_power(0,0.5)
    motors.set_power(1,0.5)
    utils.sleep(2)
    motors.set_power(0,0)
    motors.set_power(1,0)
    utils.sleep(2)
    motors.set_power(0,-0.5)
    motors.set_power(1,-0.5)


def Task_2_part_2():

    #Task 2 part 1
    def forward():
        motors.set_power(0,0.5)
        motors.set_power(1,0.5)

    def right():
        motors.set_power(0,0)

    for i in range(3):
        forward()
        utils.sleep(0.8)
        right()
        utils.sleep(0.5)

    forward()
    utils.sleep(1)
    motors.set_power(0,0)
    motors.set_power(1,0)


def Task_3():
    frontright = arduino.digital_read(11)
    while not frontright:
        set_motors(1,1)
        frontright = arduino.digital_read(11)

    print("I have hit a wall")
    set_motors(-0.5,-0.5)
    utils.sleep(0.8)
    set_motors(-0.4,0)
    utils.sleep(2)
    set_motors(0,0)


def Task_4():
    set_motors(0.5,0.5)
    while True:
        distance_left = arduino.measure_ultrasound_distance(4, 5) #This is the left sensor
        if distance_left < 500:
            set_motors(0,0.5)
            utils.sleep(0.5)
            set_motors(0,0)
            utils.sleep(0.7)
            set_motors(0.6,0.6)
            utils.sleep(1.5)
            while True:
                if distance_left < 300:
                    set_motors(1,0)
                    utils.sleep(0.5)
                    break
                distance_left = arduino.measure_ultrasound_distance(4, 5) #This is the left sensor
            break
        distance_left = arduino.measure_ultrasound_distance(4, 5) #This is the left sensor
        print(distance_left)
    set_motors(0,0)





def Task_5():
    while True:
        left_IR = arduino.analog_read(AnalogPin.A0)
        centre_IR = arduino.analog_read(AnalogPin.A1)
        right_IR = arduino.analog_read(AnalogPin.A2)
        print(left_IR, centre_IR, right_IR)
        if left_IR < 1.2 and centre_IR > 3.5 and right_IR < 1.2:
            current_state="forward"
            set_state(current_state)
        elif left_IR > 3.5 and centre_IR < 1.2 and (right_IR > 1.2 and right_IR < 3.5):
            current_state = "left"
            set_state(current_state)
        elif (left_IR > 1.2 and left_IR < 3.5)  and centre_IR < 1.2 and right_IR > 3.5  :
            current_state = "right"
            set_state(current_state)

def Task_6():
    range_data = dict()
    range_data[1] = 500
    range_data[3] = 300
    range_data[5] = 500

    for i in range(1,6,2):
        target_id = i
        set_motors(0.5,-0.5)
        while True:
            markerlist = vision.detect_markers()
            targetmarker = find_target(markerlist, target_id)

            if targetmarker != None:
                print(targetmarker)
                if targetmarker.position.distance < range_data[target_id]:
                    break
                angle_error = targetmarker.position.horizontal_angle
                if angle_error > 0.2: #target is on the right, 0.2 radians is about 11°
                    set_motors(0.5,0.3)
                elif angle_error < -0.2: #target is on the left
                    set_motors(0.5,0.3)
                else: #target is straight ahead
                    set_motors(0.4,0.4)
                    utils.sleep(0.5)
                    set_motors(0,0) #stop to take a new photo
            else: #can't see the target
                set_motors(0.5,-0.5)

def Proportional_control_for_vision():
    range_data = dict()
    range_data[1] = 500
    range_data[3] = 550
    range_data[5] = 500
    range_data[9] = 600

    Kd = 0.00125 #  distance constant
    Kp = 0.055 #  angle constant
    BASE_POWER = 0.25
    ROTATION_POWER_TO_FIND_MARKER = 0.4
    for i in range(1,6,2):
        target_id = i
        set_motors(0.3,-0.3)
        while True:
            markerlist = vision.detect_markers()
            targetmarker = find_target(markerlist, target_id)

            if targetmarker != None:
                print(targetmarker)
                if targetmarker.position.distance < range_data[target_id]:
                    break
                angle_error = targetmarker.position.horizontal_angle
                power = BASE_POWER * (targetmarker.position.distance * Kd)
                print(angle_error * Kp)
                print(power)
                if angle_error > 0.2: #target is on the right, 0.2 radians is about 11°
                   
                    set_motors(power + angle_error * Kp, power - angle_error * Kp)
                elif angle_error < -0.2: #target is on the left
                    set_motors(power - angle_error * Kp, power + angle_error * Kp)
                else: #target is straight ahead
                    set_motors(power,power)
                    #set_motors(0.4,0.4)
                    utils.sleep(0.5)
                    set_motors(0.1,0.1) #move slowly to reduce motion blur to take a new photo
            else: #can't see the target
                set_motors(ROTATION_POWER_TO_FIND_MARKER,-ROTATION_POWER_TO_FIND_MARKER)


# Helper functions for IR proportional control
class IR_readings:
    def __init__(self, left: float, centre: float, right: float):
        self.left = left
        self.centre = centre
        self.right = right

class IR_readings_queue:
    def __init__(self, size: int = 15):
        # deque automatically pushes old items out when the max length is reached
        self.history = collections.deque(maxlen=size)
        
    def add_reading(self, left: float, centre: float, right: float):
        self.history.append(IR_readings(left, centre, right))
        
    def _count_transitions(self, values: list[float], low_thresh: float, high_thresh: float) -> int:
        """
        Helper method to count how many times the values toggle between 
        a definitive LOW and a definitive HIGH state.
        """
        if len(values) < 2:
            return 0
            
        transitions = 0
        current_state = 0 # 0 = unknown, -1 = low (white), 1 = high (black)
        
        for val in values:
            new_state = 0
            if val < low_thresh:
                new_state = -1
            elif val > high_thresh:
                new_state = 1
            else:
                new_state = current_state # Keep previous state if in the middle ground
                
            # If we were in a known state, and the new state is the opposite, it's a transition
            if current_state != 0 and new_state != 0 and new_state != current_state:
                transitions += 1
                
            if new_state != 0:
                current_state = new_state
                
        return transitions

    def is_left_jittering(self, low_thresh: float = 1.5, high_thresh: float = 3.5, min_transitions: int = 3) -> bool:
        """
        Returns True if the left sensor has transitioned between high and low 
        frequently enough to be considered jittering.
        """
        left_values = [reading.left for reading in self.history]
        return self._count_transitions(left_values, low_thresh, high_thresh) >= min_transitions

    def is_right_jittering(self, low_thresh: float = 1.5, high_thresh: float = 3.5, min_transitions: int = 3) -> bool:
        """
        Returns True if the right sensor has transitioned between high and low 
        frequently enough to be considered jittering.
        """
        right_values = [reading.right for reading in self.history]
        return self._count_transitions(right_values, low_thresh, high_thresh) >= min_transitions

    
def Proportional_control_for_infrared_follow_black():
    Kp = 0.27 #  angle constant
    BASE_POWER = 0.4
    ROTATION_POWER_TO_FIND_BLACK = 0.2
    HARD_TURN_POWER = 0.05
    last_time_since_known = None
    turn_left = True
    ir_queue = IR_readings_queue(size=20)
    while True:
        left_IR = arduino.analog_read(AnalogPin.A0)
        centre_IR = arduino.analog_read(AnalogPin.A1)
        right_IR = arduino.analog_read(AnalogPin.A2)
        print(left_IR, centre_IR, right_IR)

        ir_queue.add_reading(left_IR, centre_IR, right_IR)
        power = BASE_POWER
        if ir_queue.is_left_jittering():
            current_state = "hard_left"
        elif ir_queue.is_right_jittering():
            current_state = "hard_right"
        elif left_IR < 1.2 and centre_IR > 3.5 and right_IR < 1.2:
            current_state="forward"
            #set_state(current_state)
        elif left_IR > 3.5 and centre_IR < 1.2 and (right_IR >= 1.2 and right_IR <= 3.5):
            current_state = "left"
            #set_state(current_state)
        elif (left_IR > 1.2 and left_IR < 3.5)  and centre_IR <= 1.2 and right_IR >= 3.5  :
            current_state = "right"
            #set_state(current_state)
        else:
           current_state = "unknown"
           last_time_since_known = time.time()

        if current_state == "forward":
            set_motors(power,power)
        elif current_state == "left":
            set_motors(power -  Kp, power + Kp)
        elif current_state == "right":
            set_motors(power +  Kp, power - Kp)
        elif current_state == "hard_left":
            # Apply sharper turning ratio
            set_motors(-HARD_TURN_POWER, HARD_TURN_POWER) 
        elif current_state == "hard_right":
            # Apply sharper turning ratio
            set_motors(HARD_TURN_POWER, -HARD_TURN_POWER)
        else:
            set_motors(-power * 0.1,-power * 0.1)
            if time.time() - last_time_since_known > 0.5:
                #set_motors(ROTATION_POWER_TO_FIND_BLACK,-ROTATION_POWER_TO_FIND_BLACK)
               
                utils.sleep(0.05)
                if turn_left:
                    current_state = "left"
                    #set_motors(0,ROTATION_POWER_TO_FIND_BLACK)
                else:
                    current_state = "right"
                    #set_motors(ROTATION_POWER_TO_FIND_BLACK,0)
                turn_left = not turn_left
        #utils.sleep(0.01)
        print(current_state)

class STATE(Enum):
    TRACKING = 1,
    TURNING_LEFT = 2,
    TURNING_RIGHT = 3,
    AVOIDING_OBSTACLE = 4,
    APPROACH_CAN = 5,
    ENGAGE_CAN = 6,
    SEARCHING = 7,

def PID_control(): # CONSIDER MAKING HELPER FUNCTIONS
    # CONSTANTS
    MARKER_DISTANCE_THRESHOLD = 375
    MARKER_DISTANCE_CONSTANT = 0.1
    OBSTACLE_AVOIDANCE_TIME_THRESHOLD = 0.5
    MARKER_ANGLE_CONSTANT = 0.27 #  angle constant for vision markers
    BASE_POWER = 0.4
    CAN_ENGAGEMENT_POWER = 0.6
    TRACKING_TURNING_POWER = 0.5
    SEARCHING_TURN_POWER = 0.45
    OBSTACLE_AVOIDING_POWER = 0.2
    ROTATION_POWER_TO_REVERSE_DIRECTION = 0.2
    THRESHOLD_DISTANCE = 500
    BLACK_IR_THRESHOLD = 3.5 
    WHITE_IR_THRESHOLD = 1.2
    ACTION_TIME_THRESHOLD = 0.05 # in seconds, essentially the robots reaction time
    # Pre defined variables
    state = STATE.TRACKING
    state_action_time = time.time()
    ir_queue = IR_readings_queue(size=15)
    while True:
        left_IR = arduino.analog_read(AnalogPin.A0)
        centre_IR = arduino.analog_read(AnalogPin.A1)
        right_IR = arduino.analog_read(AnalogPin.A2)
        #ir_queue.add_reading(left_IR, centre_IR, right_IR)

        distance_left = arduino.measure_ultrasound_distance(4,5)
        distance_right = arduino.measure_ultrasound_distance(6,5)
        #print(f"distance left: {distance_left}, distance right: {distance_right}")
        # Prioritize ultrasound
        if distance_left < THRESHOLD_DISTANCE and distance_right < THRESHOLD_DISTANCE:
            if state != STATE.AVOIDING_OBSTACLE:
                
                state = STATE.AVOIDING_OBSTACLE
        elif distance_left < THRESHOLD_DISTANCE or distance_right < THRESHOLD_DISTANCE:
            state = STATE.APPROACH_CAN
        else: # Then check if black line is being followed
            if centre_IR >= BLACK_IR_THRESHOLD and left_IR <= WHITE_IR_THRESHOLD and right_IR <= WHITE_IR_THRESHOLD:
                state = STATE.TRACKING
            else:
                print(left_IR,centre_IR,right_IR)
                if left_IR >= BLACK_IR_THRESHOLD and right_IR >= BLACK_IR_THRESHOLD:
                    print("Both on the line, what do I do :()")
                elif left_IR >= BLACK_IR_THRESHOLD:
                    state = STATE.TURNING_LEFT
                    state_action_time = time.time()
                elif right_IR >= BLACK_IR_THRESHOLD:
                    state = STATE.TURNING_RIGHT
                    state_action_time = time.time()
                else:
                    state = STATE.SEARCHING
                    state_action_time = time.time()
                print(state)

        if time.time() - state_action_time > ACTION_TIME_THRESHOLD:
            #print(state)
            state_action_time = time.time()
            match(state):
                case STATE.TRACKING:
                    set_motors(BASE_POWER,BASE_POWER)
                case STATE.TURNING_LEFT:
                    set_motors(BASE_POWER - TRACKING_TURNING_POWER,BASE_POWER + TRACKING_TURNING_POWER)
                case STATE.TURNING_RIGHT:
                     set_motors(BASE_POWER + TRACKING_TURNING_POWER,BASE_POWER - TRACKING_TURNING_POWER)
                case STATE.AVOIDING_OBSTACLE:
                    if time.time() - state_action_time > OBSTACLE_AVOIDANCE_TIME_THRESHOLD:
                        set_motors(-OBSTACLE_AVOIDING_POWER,-OBSTACLE_AVOIDING_POWER)
                case STATE.APPROACH_CAN: # If "can" is approached andboth ultrasound sensors detect something, then it is likely a wall
                     # There is a case of hiting a can near a wall but we will tackle this once the intial system works
                     
                     if distance_left < THRESHOLD_DISTANCE and distance_right < THRESHOLD_DISTANCE:        
                        state = STATE.AVOIDING_OBSTACLE
                     else:
                        state = STATE.ENGAGE_CAN
                case STATE.ENGAGE_CAN:
                    set_motors(CAN_ENGAGEMENT_POWER,CAN_ENGAGEMENT_POWER)
                case STATE.SEARCHING: #MAGIC NUMBERS USED AS THIS WAS COPIED FROM THE BONUS TASK, FIX!!!
                    print("searching")
                    set_motors(SEARCHING_TURN_POWER,-SEARCHING_TURN_POWER)

                    Kd = 0.00125 #  distance constant
                    Kp = 0.055 #  angle constant
                    BASE_POWER = 0.25
                    ROTATION_POWER_TO_FIND_MARKER = 0.4
                    for i in range(1,6,2):
                        target_id = i
                        set_motors(0.3,-0.3)
                        while True:
                            markerlist = vision.detect_markers()
                            targetmarker = find_target(markerlist, target_id)
                
                            if targetmarker != None:
                                print(targetmarker)
                                if targetmarker.position.distance < MARKER_DISTANCE_THRESHOLD:
                                    break
                                angle_error = targetmarker.position.horizontal_angle
                                power = BASE_POWER * (targetmarker.position.distance * Kd)
                                print(angle_error * Kp)
                                print(power)
                                if angle_error > 0.2: #target is on the right, 0.2 radians is about 11°
                                    
                                    set_motors(power + angle_error * Kp, power - angle_error * Kp)
                                elif angle_error < -0.2: #target is on the left
                                    set_motors(power - angle_error * Kp, power + angle_error * Kp)
                                else: #target is straight ahead
                                    set_motors(power,power)
                                    #set_motors(0.4,0.4)
                                    utils.sleep(0.5)
                                    set_motors(0.1,0.1) #move slowly to reduce motion blur to take a new photo
                            else: #can't see the target
                                print("cannot see marker")
                                set_motors(ROTATION_POWER_TO_FIND_MARKER,-ROTATION_POWER_TO_FIND_MARKER)



def blackness(value: float, WHITE_IR: float = 1.2, BLACK_IR: float = 3.4):
    return abs((value - WHITE_IR) / (BLACK_IR - WHITE_IR))

def move_along_line():
    Kp = 0.55
    Ki = 0.0
    Kd = 0.4125

    BASE_POWER = 0.3
    LOST_THESHOLD = 0.6
    WEIGHT_L,WEIGHT_C,WIEGHT_R = -1.0,0.0,1.0
    MAX_CORRECTION = 0.3
    SEARCH_POWER = 0.22
    SEARCH_TURN = 0.0545
    integral = 0.0
    last_time = time.time()
    last_error = 0.0
    last_error_sign = 1
    while True:
        
        left_IR_raw = arduino.analog_read(AnalogPin.A0)
        centre_IR_raw = arduino.analog_read(AnalogPin.A1)
        right_IR_raw = arduino.analog_read(AnalogPin.A2)
        
        bl,bc,br = blackness(left_IR_raw),blackness(centre_IR_raw),blackness(right_IR_raw)
        #print("-"*50)
        #print(bl,bc,br)
        now = time.time()
        dt = now - last_time
        last_time = now

        if max(bl,bc,br) < LOST_THESHOLD:
           set_motors(SEARCH_POWER + last_error_sign * SEARCH_TURN,SEARCH_POWER - last_error_sign * SEARCH_TURN )
        else:
            total = bl + bc + br
            error = (WEIGHT_L * bl + WEIGHT_C * bc + WIEGHT_R * br) / total if total > 0 else 0
            integral += error * dt
            derivative = (error - last_error) / dt if dt > 0 else 0
            correction = Kp * error + Ki * integral + Kd * derivative
            #print(correction)
            #print("-"*50)
            correction = max(-MAX_CORRECTION, min(MAX_CORRECTION,correction))
            last_error = error
            last_error_sign = 1 if error > 0 else -1
            
            set_motors(BASE_POWER + correction, BASE_POWER - correction)
        #utils.sleep(0.01)
move_along_line()