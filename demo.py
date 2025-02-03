import json
import cv2
from sklearn import neighbors
import os
import os.path
import pickle
from PIL import Image, ImageDraw
import face_recognition
import numpy as np
from data_prep import capture_and_save_image
import telegramnotification3 as tl3
from datetime import datetime, time

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'JPG', "pgm"}

def get_knn_classifier(model_path):
    with open(model_path, 'rb') as f:
        knn_classifier = pickle.load(f)
    return knn_classifier

def get_matches(knn_classifier, distance_threshold, face_locations, faces_encodings):
    closest_distances = knn_classifier.kneighbors(faces_encodings, n_neighbors=1)
    are_matches = [closest_distances[0][i][0] <= distance_threshold for i in range(len(face_locations))]
    return are_matches

def predict_knn(frame, knn_classifier=None, model_path=None, distance_threshold=0.5):
    if knn_classifier is None and model_path is None:
        raise Exception("No KNN classifier passed")

    if knn_classifier is None:
        knn_classifier = get_knn_classifier(model_path)

    face_locations = face_recognition.face_locations(frame)

    if len(face_locations) == 0:
        return []

    faces_encodings = face_recognition.face_encodings(frame, known_face_locations=face_locations)

    are_matches = get_matches(knn_classifier, distance_threshold, face_locations, faces_encodings)

    return [(pred, loc) if rec else ("unknown", loc) for pred, loc, rec in zip(knn_classifier.predict(faces_encodings), face_locations, are_matches)]

def show_prediction_labels_on_image(frame, predictions):
    pil_image = Image.fromarray(frame)
    draw = ImageDraw.Draw(pil_image)

    for name, (top, right, bottom, left) in predictions:
        top *= 2
        right *= 2
        bottom *= 2
        left *= 2
        draw.rectangle(((left, top), (right, bottom)), outline=(0, 0, 255))
        name = name.encode("UTF-8")

        text_width, text_height = draw.textsize(name)
        draw.rectangle(((left, bottom - text_height - 10), (right, bottom)), fill=(0, 0, 255), outline=(0, 0, 255))
        draw.text((left + 6, bottom - text_height - 5), name, fill=(255, 255, 255, 255))

    del draw

    opencvimage = np.array(pil_image)
    return opencvimage

def get_roles_from_json(json_file):
    with open(json_file, "r") as f:
        roles_dict = json.load(f)
    return roles_dict

def get_role(name):
    json_file = "roles.json"
    if name == "unknown":
        return None
    if os.path.exists(json_file):
        roles_dict = get_roles_from_json(json_file)
    else:
        return None

    return roles_dict[name]

def get_image():
    cap = cv2.VideoCapture(0)  # Access the laptop's webcam
    if not cap.isOpened():
        print("Error: Unable to open video source.")
        exit(1)
    filename = capture_and_save_image("unknown", 1, cap)  # Use cap instead of webcam
    cap.release()
    cv2.destroyAllWindows()
    return filename

def handle_unknown_person():
    image = get_image()
    text = 'Hi! Unknown Person at the door \n Do you want to Allow / Deny.'
    tl3.messaging(text, image)

def handle_known_person(name, starttime, endtime):
    nowtime = datetime.now().time()
    if time(starttime) <= nowtime <= time(endtime):
        tl3.telegram_bot_sendtext(f"Known person {name} at door. Letting them in.")
    else:
        tl3.known_person_wrong_time(f"Known person {name} at door but wrong timing. Allow/Deny?")

def handle_family_person(predicted_name):
    tl3.telegram_bot_sendtext(f"{predicted_name} has been let into house")

def main():
    process_this_frame = 0
    print('Setting cameras up...')
