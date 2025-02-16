import cv2
import os
from tkinter import filedialog
import shutil

current_dir = os.path.dirname(os.path.abspath(__file__))

frontal_cascade_path = "./haarcascade_frontalface_default.xml"
left_cascade_path = "./haarcascade_profileface.xml"
right_cascade_path = "./haarcascade_profileface.xml"

frontal_cascade = cv2.CascadeClassifier(frontal_cascade_path)
left_cascade = cv2.CascadeClassifier(left_cascade_path)
right_cascade = cv2.CascadeClassifier(right_cascade_path)

global_image_count = 0

def add_face_to_dataset(image, dataset_path, source="camera", user_id=None):
    global global_image_count
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    frontal_faces = frontal_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
    left_faces = left_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
    right_faces = right_cascade.detectMultiScale(cv2.flip(gray, 1), scaleFactor=1.3, minNeighbors=5)
    
    for (x, y, w, h) in frontal_faces:
        filename = f'User_{user_id}_{global_image_count}.jpg'
        cv2.imwrite(os.path.join(dataset_path, filename), gray[y:y+h, x:x+w])
        cv2.rectangle(image, (x, y), (x+w, y+h), (50, 50, 255), 1)
        global_image_count += 1

    for (x, y, w, h) in left_faces:
        filename = f'User_{user_id}_{global_image_count}.jpg'
        cv2.imwrite(os.path.join(dataset_path, filename), gray[y:y+h, x:x+w])
        cv2.rectangle(image, (x, y), (x+w, y+h), (50, 255, 50), 1)
        global_image_count += 1

    for (x, y, w, h) in right_faces:
        x = gray.shape[1] - x - w
        filename = f'User_{user_id}_{global_image_count}.jpg'
        cv2.imwrite(os.path.join(dataset_path, filename), gray[y:y+h, x:x+w])
        cv2.rectangle(image, (x, y), (x+w, y+h), (255, 50, 50), 1)
        global_image_count += 1
    
    cv2.imshow("Detected Faces", image)

def scan_faces_from_camera(dataset_path, max_images=300):
    video = cv2.VideoCapture(0)
    user_id = input("Enter user ID: ")
    count = 0
    while count < max_images:
        ret, frame = video.read()
        if not ret:
            print("Error: Failed to capture frame")
            break
        add_face_to_dataset(frame, dataset_path, source="camera", user_id=user_id)
        count += 1
        k = cv2.waitKey(1)
        if k == ord('q') or k == 27:
            break
        if count >= max_images:
            break
        
    video.release()
    cv2.destroyAllWindows()

def scan_faces_from_external_directory(dataset_path):
    user_id = input("Enter user ID: ")
    external_path = filedialog.askdirectory(title="Select External Directory")
    if external_path:
        for file in os.listdir(external_path):
            if file.endswith(".jpg") or file.endswith(".png"):
                image_path = os.path.join(external_path, file)
                image = cv2.imread(image_path)
                if image is not None:
                    filename = f'User_{user_id}_{os.path.basename(image_path)}'
                    shutil.copy(image_path, os.path.join(dataset_path, filename))
                else:
                    print(f"Error: Unable to read image file '{image_path}'")

def main():
    print("Choose an option:")
    print("1. Scan faces from camera")
    print("2. Scan faces from external directory")
    choice = input("Enter your choice (1 or 2): ")

    dataset_path = "./datasets"
    if not os.path.exists(dataset_path):
        os.makedirs(dataset_path)

    if choice == '1':
        scan_faces_from_camera(dataset_path)
    elif choice == '2':
        scan_faces_from_external_directory(dataset_path)
    else:
        print("Invalid choice. Please enter either '1' or '2'.")

if __name__ == "__main__":
    main()
