import cv2
import mediapipe as mp
import platform
import math

target_OS = platform.system()
if target_OS == "Windows":
	print("Estás usando Windows")
elif target_OS == "Linux":
	import evdev
	import uinput

	device = uinput.Device([
		uinput.BTN_A,
		# uinput.BTN_TR,
		# uinput.BTN_TL,
		uinput.BTN_TRIGGER,
		uinput.ABS_X + (0, 255, 0, 0),  # X axis of left joystick
		uinput.ABS_Y + (0, 255, 0, 0)   # Y axis of left joystick
	])
	device.emit(uinput.BTN_A, 1)
	print("Estás usando Linux")

mp_hands = mp.solutions.hands.Hands()
mpDraw = mp.solutions.drawing_utils

camera_index = 0
cam = cv2.VideoCapture(camera_index)

q_unicode = ord('q')

middle_finger_knuckle_index = 9 
hand_bottom_index = 0

def calculate_distance(p1, p2):
	return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def check_is_hand_open(hand_landmarks):
	# Get reference points coords
	landmarks = [(lm.x, lm.y) for lm in hand_landmarks.landmark]
	
	# Define finger indexes
	finger_tips = [8, 12, 16, 20]  # Index, middle, ring, little finger
	
	distances = []
	for i in range(len(finger_tips) - 1):
		for j in range(i + 1, len(finger_tips)):
			dist = calculate_distance(landmarks[finger_tips[i]], landmarks[finger_tips[j]])
			distances.append(dist)
	
	# Check if hand is open or close based on the distances
	average_distance = sum(distances) / len(distances)
	print(f'Average distance: {average_distance}')
	return average_distance > 0.06  # 0.05 is the closing reference value


def calculate_middle_point(pt1, pt2):
	x1, y1 = pt1
	x2, y2 = pt2
	x_diff = abs(x1 - x2)
	y_diff = abs(y1 - y2)

	new_x = int(x2 + x_diff/2) if x1 > x2 else int(x1 + x_diff/2)
	new_y = int(y2 + y_diff/2) if y1 > y2 else int(y1 + y_diff/2)

	return (new_x, new_y)
	

def linear_scaling(x, minA=-500, maxA=500, minB=0, maxB=255):
	new_x = (x - minA) / (maxA - minA) * (maxB - minB) + minB
	return new_x


while True:
	_, frame = cam.read()
	frame_h, frame_w, _ = frame.shape
	frame_center_coords = (int(frame_w/2), int(frame_h/2))
	frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
	results = mp_hands.process(frame_rgb)

	if results.multi_hand_landmarks:
	# Hands were detected
		print("Yes")
		for hand_landmarks in results.multi_hand_landmarks:  
			is_hand_open = check_is_hand_open(hand_landmarks)
			mpDraw.draw_landmarks(frame ,hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
			hand_landmarks_list = []
			for id, lm in enumerate(hand_landmarks.landmark):
				hand_landmarks_list.append({"id": id, "landmark": lm })
				
			middle_finger_knuckle_lm = hand_landmarks_list[middle_finger_knuckle_index]["landmark"]
			hand_bottom_lm = hand_landmarks_list[hand_bottom_index]["landmark"]

			# Convertir coordenadas normalizadas en píxeles
			middle_finger_knuckle_coords = (int(middle_finger_knuckle_lm.x * frame_w), int(middle_finger_knuckle_lm.y * frame_h))
			hand_bottom_coords = (int(hand_bottom_lm.x * frame_w), int(hand_bottom_lm.y * frame_h))
			hand_center_coords = calculate_middle_point(middle_finger_knuckle_coords, hand_bottom_coords)

			cv2.circle(frame, hand_center_coords, 5, (255, 0, 0), cv2.FILLED)
			cv2.circle(frame, frame_center_coords, 5, (0, 255, 0), cv2.FILLED)
			cv2.line(frame, frame_center_coords, hand_center_coords, (255, 0, 0), 3)

			# print(get_distance_between_points(hand_center_coords, frame_center_coords))
			print(f'Middle finger {middle_finger_knuckle_coords}')
			print(f'Hand bottom {hand_bottom_coords}')
			print(f'Hand center {hand_center_coords}')
			
			joystick_input = {
				"x": int(linear_scaling(hand_center_coords[0] - frame_center_coords[0], -int(frame_w/4), int(frame_w/4), 0, 255)),
				"y": int(linear_scaling(hand_center_coords[1] - frame_center_coords[1], -int(frame_h/4), int(frame_h/4), 0, 255))
			}
			print(f'Joystick: x = {joystick_input["x"]}, y = {joystick_input["y"]}')
			print(f'Is Hand open?: {is_hand_open}')
			device.emit(uinput.ABS_X, joystick_input["x"])
			device.emit(uinput.ABS_Y, joystick_input["y"])
			device.emit(uinput.BTN_TRIGGER, int(not is_hand_open))
			# device.emit(uinput.BTN_TL, int(is_hand_open))
			# # Mostrar coordenadas en consola
			# print(f'Landmark {id}: ({cx}, {cy})')

			# if id == 9:

	else:
		# No hands were detected
		# print("No")
		device.emit(uinput.ABS_X, 128)
		device.emit(uinput.ABS_Y, 128)
		device.emit(uinput.BTN_TRIGGER, 0)
		...

	cv2.imshow('Hand Gamepad v0.1', frame)

	key = cv2.waitKey(1)
	if key == q_unicode:
		break

cam.release()
cv2.destroyAllWindows()