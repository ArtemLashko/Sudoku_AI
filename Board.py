import operator

import cv2
import time
import numpy as np
import keras
from keras.models import load_model
from keras.preprocessing import image
from keras.models import model_from_json
from SolveSudoku import sudoku_solver
import os

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
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


class Board:
    #TESTING = True

    def __init__(self, cv2_image, test=False):
        self.TESTING = test
        if self.TESTING:
            self.loaded_model = load_model("best_mnist.h5")
        else:
            self.loaded_model = load_model("mlp_digits.h5")
        self.loaded_model.summary()
        print("Loaded saved model from disk.")
        self.board_image = cv2_image

    def center_image(self, img):
        rows, cols = img.shape
        image_temp = img.copy()

        for i in range(rows):
            for j in range(cols):
                image_temp[i, j] = 0

        x_axis = set()
        y_axis = set()

        for i in range(rows):
            for j in range(cols):
                if img[i, j]:
                    x_axis.add(i)
                    y_axis.add(j)

        if len(x_axis) == 0:  # we have no white pixel on our image
            return img

        x_axis = sorted(list(x_axis))
        y_axis = sorted(list(y_axis))


        # median elements for x-axis, y-axis
        n = x_axis[len(x_axis) // 2]
        m = y_axis[len(y_axis) // 2]

        n_org = rows // 2
        m_org = cols // 2

        # Ideal center of the image is [n_org, m_org]
        # Our center is [n, m]
        # now we have to move all points towards it
        # so we need to do n = n_org, m = m_org
        x_dict = dict()
        y_dict = dict()

        for x in x_axis:
            delta_x = n - x
            x_dict[x] = n_org - delta_x

        for y in y_axis:
            delta_y = m - y
            y_dict[y] = m_org - delta_y

        # now let's apply transformation
        for i in range(rows):
            for j in range(cols):
                if img[i, j]:
                    new_x = x_dict[i]
                    new_y = y_dict[j]
                    image_temp[new_x, new_y] = img[i, j]

        return image_temp

    def extract_features(self, img):
        debug(img, "images/cell2.jpg")
        rows, cols = img.shape
        image_temp = img.copy()
        for i in range(rows):
            for j in range(cols):
                image_temp[i, j] = 0
        full_black_image = image_temp.copy()

        h, w = img.shape[:2]
        margin = 0
        for i in range(margin, rows - margin):
            for j in range(margin, cols - margin):
                temp = img[i, j] / 255.0
                if temp > 0.5:
                    image_temp[i, j] = 255
        used = [[0 for i in range(cols)] for j in range(rows)]

        center_margin = int(np.mean([h, w]) / 2.5)
        result = full_black_image.copy()

        def check(x, y, rows, columns):
            if (x >= rows) or (y >= columns) or (y < 0) or (x < 0):
                return False
            return True

        def dfs(x, y, alpha):
            rows, cols = image_temp.shape
            used[x][y] = 1
            result[x, y] = image_temp[x, y]
            for i in range(-alpha, alpha):
                for j in range(-alpha, alpha):
                    new_x = x + i
                    new_y = y + j
                    if (check(new_x, new_y, rows, cols) and
                            image_temp[new_x, new_y] and (not used[new_x][new_y])):
                        dfs(new_x, new_y, alpha)

        for i in range(center_margin, rows - center_margin):
            for j in range(center_margin, cols - center_margin):
                if image_temp[i, j] == 255 and (not used[i][j]):
                    dfs(i, j, 2)
        return result

    def identify_number(self, image):
        image_resize = cv2.resize(image, (28, 28))  # For plt.imshow
        contours, h = cv2.findContours(image_resize, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        # area = cv2.contourArea(contours[0])
        if self.TESTING:
            image_resize_2 = np.reshape(image_resize, (1, 28, 28, 1)).astype("float32")
        else:
            image_resize_2 = np.expand_dims(image_resize, axis=0).astype(
                "float32")  # For input to model.predict_classes
        image_resize_2 /= 255.0
        res = self.loaded_model.predict(image_resize_2)
        res[0][0] = 0
        y_predict = np.argmax(res, axis=-1)
        print('Prediction of loaded_model: {}'.format(y_predict))
        return max(1, y_predict)

    def get_res(self):
        self.grid = self.extract_number(self.board_image)
        print(self.grid)
        sudoku_solver(self.grid)

    # Extract numbers from a square grid
    def extract_number(self, sudoku):
        sudoku = cv2.resize(sudoku, (450, 450))

        # Go cell by cell
        grid = np.zeros([9, 9])
        for i in range(9):
            for j in range(9):
                image = sudoku[i * 50:(i + 1) * 50, j * 50:(j + 1) * 50]

                debug(image, "images/cell1.jpg")

                # Extracting a largest feature
                image_revised = self.extract_features(image)
                debug(image_revised, "images/cell3.jpg")
                # If our image contains a digit, it will have sum > 3000
                if image_revised.sum() > 3000:
                    # Now we need to center our image
                    centered_image = self.center_image(image_revised)
                    debug(centered_image, "images/cell4.jpg")
                    grid[i][j] = self.identify_number(centered_image)
                else:
                    grid[i][j] = 0

        return grid.astype(int)
