import cv2
import mediapipe as mp
import platform
import math

target_OS = platform.system()
if target_OS == "Windows":
	print("SO: Windows")
elif target_OS == "Linux":
	import evdev
	import uinput

	device = uinput.Device([
		uinput.BTN_A,		# B / Circle
		uinput.BTN_B,		# X / Square
		uinput.BTN_C,		# Y / Triangle
		uinput.BTN_DEAD,	# A / X
		uinput.BTN_Y,		# R1
		uinput.BTN_X,		# L1
		uinput.BTN_TL,		# R2
		uinput.BTN_Z,		# L2
		uinput.BTN_TL2,		# Select
		uinput.BTN_START,	# Start
		
		# Left Joystick
		uinput.ABS_X + (0, 255, 0, 0),  # X axis of left joystick
		uinput.ABS_Y + (0, 255, 0, 0),  # Y axis of left joystick
		# Right Joystick
		uinput.ABS_RX + (0, 255, 0, 0),  # X axis of right joystick
		uinput.ABS_RY + (0, 255, 0, 0)   # X axis of right joystick
	])
	device.emit(uinput.BTN_A, 1)
	print("SO: Linux")


# Load hands detector object
mp_hands = mp.solutions.hands.Hands()
# Load drawing object
mpDraw = mp.solutions.drawing_utils

camera_index = 0
cam = cv2.VideoCapture(camera_index)


# Get the distance bewteen two points
def calculate_distance(p1, p2):
	return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def check_is_hand_open(hand_landmarks):
	# Get reference points coords
	landmarks = [(lm.x, lm.y) for lm in hand_landmarks.landmark]
	
	# Define finger indexes
	finger_tips = [8, 12, 16, 20]  # Index, middle, ring, little finger
	
	# Get finger distances
	distances = []
	for i in range(len(finger_tips) - 1):
		for j in range(i + 1, len(finger_tips)):
			dist = calculate_distance(landmarks[finger_tips[i]], landmarks[finger_tips[j]])
			distances.append(dist)
	
	# Check if hand is open or close based on the distances
	average_distance = sum(distances) / len(distances)
	print(f'Average distance: {average_distance}')
	return average_distance > 0.1  # 0.05 is the closing reference value


# Calculate a middle point between to points
def calculate_middle_point(pt1, pt2):
	x1, y1 = pt1
	x2, y2 = pt2
	x_diff = abs(x1 - x2)
	y_diff = abs(y1 - y2)

	new_x = int(x2 + x_diff/2) if x1 > x2 else int(x1 + x_diff/2)
	new_y = int(y2 + y_diff/2) if y1 > y2 else int(y1 + y_diff/2)

	return (new_x, new_y)
	

# Transform distance from hand to the center of the image into joystick data
def linear_scaling(x, minA=-500, maxA=500, minB=0, maxB=255):
	new_x = (x - minA) / (maxA - minA) * (maxB - minB) + minB
	return new_x


def set_controller_input_linux(device, input_data_left, input_data_right):
	# Set left hand input
	device.emit(uinput.ABS_X, input_data_left["joystick_x"])
	device.emit(uinput.ABS_Y, input_data_left["joystick_y"])
	device.emit(uinput.BTN_Z, int(not input_data_left["is_hand_open"]))

	# Set right hand input
	device.emit(uinput.ABS_RX, input_data_right["joystick_x"])
	device.emit(uinput.ABS_RY, input_data_right["joystick_y"])
	device.emit(uinput.BTN_TL, int(not input_data_right["is_hand_open"]))


def get_input_from_frame(frame):
	# Constants
	MIDDLE_FINGER_KNUCKLE_INDEX = 9 
	HAND_BOTTOM_INDEX = 0

	# Get frame data
	frame_h, frame_w, _ = frame.shape
	frame_center_coords = (frame_w//2, frame_h//2)
	frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
	results = mp_hands.process(frame_rgb)

	if results.multi_hand_landmarks: # Hands were detected
		for hand_landmarks in results.multi_hand_landmarks:  
			# Draw hand landmarks
			mpDraw.draw_landmarks(frame ,hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)

			is_hand_open = check_is_hand_open(hand_landmarks)

			# Generate a list of every landmark
			hand_landmarks_list = []
			for id, lm in enumerate(hand_landmarks.landmark):
				hand_landmarks_list.append({"id": id, "landmark": lm })
				
			middle_finger_knuckle_lm = hand_landmarks_list[MIDDLE_FINGER_KNUCKLE_INDEX]["landmark"]
			hand_bottom_lm = hand_landmarks_list[HAND_BOTTOM_INDEX]["landmark"]

			# Transform landmark coords into pixel coords
			middle_finger_knuckle_coords = (int(middle_finger_knuckle_lm.x * frame_w), int(middle_finger_knuckle_lm.y * frame_h))
			hand_bottom_coords = (int(hand_bottom_lm.x * frame_w), int(hand_bottom_lm.y * frame_h))
			hand_center_coords = calculate_middle_point(middle_finger_knuckle_coords, hand_bottom_coords)

			# Draw visual references
			cv2.circle(frame, hand_center_coords, 3, (255, 0, 0), cv2.FILLED)
			cv2.circle(frame, frame_center_coords, 3, (0, 255, 0), cv2.FILLED)
			cv2.line(frame, frame_center_coords, hand_center_coords, (255, 0, 0), 2)

			# Get hand joystick data
			joystick_input = {
				"x": int(linear_scaling(hand_center_coords[0] - frame_center_coords[0], -frame_w//4, frame_w//4, 0, 255)),
				"y": int(linear_scaling(hand_center_coords[1] - frame_center_coords[1], -frame_h//5, frame_h//5, 0, 255))
			}


			# Build input data dict
			input_data = {
				"is_hand_open": is_hand_open,
				"joystick_x": joystick_input["x"],
				"joystick_y": joystick_input["y"]
			}

			# DEBUG INFO
			# print(f'Middle finger {middle_finger_knuckle_coords}')
			# print(f'Hand bottom {hand_bottom_coords}')
			# print(f'Hand center {hand_center_coords}')
			# print(f'Joystick: x = {joystick_input["x"]}, y = {joystick_input["y"]}')
			# print(f'Is Hand open?: {is_hand_open}')
			return input_data

	else: # No hands were detected
		input_data = {
				"is_hand_open": 1,
				"joystick_x": 128,
				"joystick_y": 128
		}
		
		return input_data


q_unicode = ord('q')
p_unicode = ord('p')
in_pause = False
while True:
	_, frame = cam.read()
	frame = cv2.flip(frame, 1)
	h, w, channels = frame.shape
	half = w//2
	left_hand_frame = frame[:, :half] 
	right_hand_frame = frame[:, half:]  
	if not in_pause:
		# Get input data from both hands
		left_input = get_input_from_frame(left_hand_frame)
		right_input = get_input_from_frame(right_hand_frame)
		print(left_input)
		print(right_input)
		
		# Set input data on virtual controller
		set_controller_input_linux(device, left_input, right_input) 
	 

	cv2.imshow('Gamehand v0.2', frame)

	key = cv2.waitKey(1)
	if key == p_unicode:
		in_pause = not in_pause
	if key == q_unicode:
		break

cam.release()
cv2.destroyAllWindows()