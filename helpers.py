import math

# Get the distance bewteen two points
def calculate_distance(p1, p2):
	return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


# Calculate a middle point between to points
def calculate_middle_point(pt1, pt2):
	x1, y1 = pt1
	x2, y2 = pt2
	x_diff = abs(x1 - x2)
	y_diff = abs(y1 - y2)

	new_x = int(x2 + x_diff/2) if x1 > x2 else int(x1 + x_diff/2)
	new_y = int(y2 + y_diff/2) if y1 > y2 else int(y1 + y_diff/2)

	return (new_x, new_y)
	
# Transform a value from set A to its equivalent on set B
def linear_scaling(x, minA=-500, maxA=500, minB=0, maxB=255):
	return (x - minA) / (maxA - minA) * (maxB - minB) + minB
