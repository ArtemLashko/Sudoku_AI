import operator
import cv2
import numpy as np
import time

# Use ESC to close app window
ESC_KEY = 27


def debug(x, filename):
    image_path = r'"C:\Users\ilart\Downloads\SudokuAI\"'
    cv2.imshow('Image', x)
    # Using cv2.imwrite() method
    # Saving the image
    cv2.imwrite(filename, x)
    while True:
        if cv2.waitKey(1) & 0xFF == ESC_KEY:
            break
        time.sleep(0.1)


class Parser:
    def prepare_image(self):
        # Gaussian blur with a kernal size (height, width) of 11.
        # Kernal sizes = odd sides and it should be a square
        gblured_img = cv2.GaussianBlur(self.original_img, (11, 11), 0)
        # Adaptive threshold using 11 nearest neighbour pixels
        thresholed_img = cv2.adaptiveThreshold(gblured_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11,
                                               2)

        # Right now our blur_img has white cells and black text, let's invert it

        thresholed_img = cv2.bitwise_not(thresholed_img, thresholed_img)

        result = cv2.dilate(thresholed_img, self.kernel)

        return result

    def __init__(self, image_file):
        self.original_img = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE)
        # get a kernel
        # self.kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        self.kernel = np.array([[0., 1., 0.], [1., 1., 1.], [0., 1., 0.]], np.uint8)

        # Prepare our image
        self.prepared_image = self.prepare_image()
        debug(self.prepared_image, "images/2.jpg")

        # debug(self.prepared_image)
        # debug(pre_process_image(self.original_img))

        self.res = self.parse_board()

    def get_result(self):
        return self.res

    # This function extracts a square board from a picture
    def parse_board(self):
        res = self.find_the_board()
        debug(res, "images/3.jpg")
        res_inverted = cv2.bitwise_not(res, res)
        debug(res_inverted, "images/4.jpg")
        # return res_inverted
        return res

    def find_the_board(self):
        sides = self.find_max_polygon()
        # print(sides)
        # print(find_corners_of_largest_polygon(self.prepared_image))
        result = self.crop(sides)
        return result

    def distance_between(self, p1, p2):
        """Returns the scalar distance between two points"""
        a = p2[0] - p1[0]
        b = p2[1] - p1[1]
        return np.sqrt((a * a) + (b * b))

    def find_max_polygon(self):
        contours, h = cv2.findContours(self.prepared_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        # we need to have at least one contour
        # Since our array of contours is already sorted, the largest polygon will be first

        if len(contours) > 0:
            max_polygon = contours[0]
        else:
            return False
        # bottom right = max(x + y)
        bottom_right, _ = max(enumerate([pt[0][0] + pt[0][1] for pt in max_polygon]), key=operator.itemgetter(1))
        # top left = min(x + y)
        top_left, _ = min(enumerate([pt[0][0] + pt[0][1] for pt in max_polygon]), key=operator.itemgetter(1))
        # bottom_left = min(x - y)
        bottom_left, _ = min(enumerate([pt[0][0] - pt[0][1] for pt in max_polygon]), key=operator.itemgetter(1))
        # top_right = max(x - y)
        top_right, _ = max(enumerate([pt[0][0] - pt[0][1] for pt in max_polygon]), key=operator.itemgetter(1))

        sides = [max_polygon[top_left][0], max_polygon[top_right][0],
                 max_polygon[bottom_right][0], max_polygon[bottom_left][0]]
        return sides

    def crop(self, sides):
        """Crops and warps a rectangular section from an image into a square of similar size."""

        # Rectangle described by top left, top right, bottom right and bottom left points
        top_left, top_right, bottom_right, bottom_left = sides[0], sides[1], sides[2], sides[3]

        # Explicitly set the data type to float32 or `getPerspectiveTransform` will throw an error
        src = np.array([top_left, top_right, bottom_right, bottom_left], dtype='float32')

        # Get the longest side in the rectangle
        side = max([
            self.distance_between(top_left, bottom_left),
            self.distance_between(bottom_right, top_right),
            self.distance_between(top_left, top_right),
            self.distance_between(bottom_right, bottom_left)
        ])

        dst = np.array([[0, 0], [side - 1, 0], [side - 1, side - 1], [0, side - 1]], dtype='float32')

        # 4 Point OpenCV getPerspective Transform
        m = cv2.getPerspectiveTransform(src, dst)

        # Cut it out from the original image
        return cv2.warpPerspective(self.original_img, m, (int(side), int(side)))
