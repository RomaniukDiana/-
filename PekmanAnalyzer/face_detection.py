import cv2
import dlib
import numpy as np
from PIL import Image

def preprocess_image(image_path):
    img = Image.open(image_path)

    cv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)

    detector = dlib.get_frontal_face_detector()

    faces = detector(cv_image)

    if faces:
        face = faces[0]
        x, y, w, h = face.left(), face.top(), face.width(), face.height()
        face_roi = cv_image[y:y + h, x:x + w]

        face_roi = cv2.resize(face_roi, (48, 48))

        face_array = np.expand_dims(face_roi, axis=0)
        face_array = np.expand_dims(face_array, axis=-1)

        return face_array
    else:
        print("Обличчя не знайдено на зображенні")