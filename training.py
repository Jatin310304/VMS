
import math
from sklearn import neighbors
import os
import os.path
import pickle
import face_recognition
from face_recognition.face_recognition_cli import image_files_in_folder


allowed_extensions = {'png', 'jpg', 'jpeg', 'JPG'}

def is_directory(training_dir, class_dir):
    return os.path.isdir(os.path.join(training_dir, class_dir))

def training_knn(training_dir, model_dest_path=None, n_neighbors=None, knn_algo='ball_tree'):
    X = []
    y = []

    for class_dir in os.listdir(training_dir):
        if not is_directory(training_dir, class_dir):
            continue

        directory_path = os.path.join(training_dir, class_dir)
        for img_path in image_files_in_folder(directory_path):
            image = face_recognition.load_image_file(img_path)
            face_bounding_boxes = face_recognition.face_locations(image)

            if len(face_bounding_boxes) != 1:

                continue
            else:

                X.append(face_recognition.face_encodings(
                    image, known_face_locations=face_bounding_boxes)[0])
                y.append(class_dir)

    if n_neighbors is None:
        n_neighbors = int(round(math.sqrt(len(X))))

    knn_clf = neighbors.KNeighborsClassifier(
        n_neighbors=n_neighbors, algorithm=knn_algo, weights='distance')
    knn_clf.fit(X, y)

    if model_dest_path is not None:
        with open(model_dest_path, 'wb') as f:
            pickle.dump(knn_clf, f)

    return knn_clf

def main():
    print("Training KNN classifier")
    classifier = training_knn(
        "image dataset", model_dest_path="trained_knn_model.clf", n_neighbors=2)
    print("Training complete!")

if __name__ == "__main__":
    main()