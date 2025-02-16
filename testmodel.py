import cv2
import numpy as np
from datetime import datetime
import mysql.connector
from fpdf import FPDF
import tkinter as tk
from tkinter import ttk, filedialog
import threading
import time
import os

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Immun0calypse"
)

def create_database_table_and_save_as_pdf(host, user, password, database):
    try:
        with mydb.cursor() as mycursor:
            mycursor.execute("CREATE DATABASE IF NOT EXISTS {}".format(database))
            mycursor.execute("USE {}".format(database))

            mycursor.execute("""
                CREATE TABLE IF NOT EXISTS Attendance_Sheet (
                    Serial_Number INT AUTO_INCREMENT PRIMARY KEY,
                    Name VARCHAR(255),
                    Matric_Number VARCHAR(255),
                    Department_Name VARCHAR(255)
                )
            """)
            mydb.commit()
    except mysql.connector.Error as err:
        print("Error creating database and table:", err)

def add_student_record(name, matric_number, department_name):
    try:
        with mydb.cursor() as mycursor:
            mycursor.execute("SELECT * FROM Attendance_Sheet WHERE Name = %s AND Matric_Number = %s AND Department_Name = %s", (name, matric_number, department_name))
            existing_record = mycursor.fetchone()
            if not existing_record:
                sql = "INSERT INTO Attendance_Sheet (Name, Matric_Number, Department_Name) VALUES (%s, %s, %s)"
                val = (name, matric_number, department_name)
                mycursor.execute(sql, val)
                mydb.commit()
    except mysql.connector.Error as err:
        print("Error adding student record to the database:", err)

def fetch_table_data():
    try:
        with mydb.cursor() as mycursor:
            mycursor.execute("SELECT * FROM Attendance_Sheet")
            result = mycursor.fetchall()
            return result
    except mysql.connector.Error as err:
        print("Error fetching table data:", err)
        return []

def save_as_pdf(filename, data, headers):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    today = datetime.today().strftime('%Y-%m-%d')
    pdf.cell(200, 10, "ATTENDANCE SHEET for " + today, ln=True, align='C')
    pdf.ln(10)

    for header in headers:
        pdf.cell(40, 10, header, border=1)
    pdf.ln()

    idx = 1
    for row in data:
        pdf.cell(40, 10, str(idx), border=1)
        for i, item in enumerate(row):
            if i == 1:
                pdf.cell(40, 10, str(item), border=1)
            elif i != 0:
                pdf.cell(40, 10, str(item), border=1)
        pdf.ln()
        idx += 1

    pdf.output(filename)

def display_table_in_app():
    root = tk.Tk()
    root.title("ATTENDANCE SHEET")
    headers = ["Serial Number", "Name", "Matric Number", "Department Name"]
    today = datetime.today().strftime('%Y-%m-%d')

    header_frame = tk.Frame(root)
    header_frame.pack()

    header_label = tk.Label(header_frame, text="ATTENDANCE SHEET for " + today, font=("Arial", 14, "bold"))
    header_label.pack(pady=10)

    frame = ttk.Frame(root)
    frame.pack(fill="both", expand=True)

    tree = ttk.Treeview(frame, columns=headers, show="headings")

    yscroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    yscroll.pack(side="right", fill="y")
    tree.configure(yscrollcommand=yscroll.set)

    for header in headers:
        tree.heading(header, text=header, anchor='center')
    tree.pack(expand=True, fill="both")

    def update_table():
        while not opencv_window_closed:
            try:
                data = fetch_table_data()
                if data is not None:
                    tree.delete(*tree.get_children())
                    for idx, row in enumerate(data, start=1):
                        tree.insert("", tk.END, values=(idx,) + row[1:])
                time.sleep(1)
            except Exception as e:
                print("Error updating table:", e)
    threading.Thread(target=update_table, daemon=True).start()

    def save_pdf_button_clicked():
        filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if filename:
            data = fetch_table_data()
            save_as_pdf(filename, data, headers)

    def clear_table_button_clicked():
        try:
            with mydb.cursor() as mycursor:
                mycursor.execute("TRUNCATE TABLE Attendance_Sheet")
                mydb.commit()
                tree.delete(*tree.get_children())
        except mysql.connector.Error as err:
            print("Error clearing table data:", err)

    save_pdf_button = tk.Button(root, text="Save as PDF", command=save_pdf_button_clicked)
    save_pdf_button.pack()

    clear_table_button = tk.Button(root, text="Clear Table", command=clear_table_button_clicked)
    clear_table_button.pack()

    root.mainloop()


student_info = {
    "Philip": ("M123", "Computer Science"),
    "Tobi": ("M456", "Engineering"),
    "David": ("M789", "Mathematics"),
    "Divine": ("M012", "Physics")
}
name_list = ["", "Philip", "Tobi", "David", "Divine"]

def face_recognition():
    global opencv_window_closed
    video = cv2.VideoCapture(0)
    frontal_cascade = cv2.CascadeClassifier("./haarcascade_frontalface_default.xml")
    left_cascade = cv2.CascadeClassifier("./haarcascade_profileface.xml")
    right_cascade = cv2.CascadeClassifier("./haarcascade_profileface.xml")
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("./Trainer.yml")

    tracked_faces = {}  # Dictionary to track detected faces

    while True:
        ret, frame = video.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect frontal faces
        frontal_faces = frontal_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in frontal_faces:
            serial, conf = recognizer.predict(gray[y:y+h, x:x+w])
            if conf < 50:
                name = name_list[serial]
                matric_number, department_name = student_info.get(name, ("Unknown", "Unknown"))
                add_student_record(name, matric_number, department_name)
                if serial not in tracked_faces:  # If face not tracked yet
                    tracked_faces[serial] = (x, y, w, h)  # Add to tracked faces
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (50, 50, 255), 1)
                    cv2.putText(frame, name, (x, y-40), cv2.FONT_HERSHEY_SIMPLEX, 1, (50, 50, 255), 2)
            else:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 1)  # Red rectangle for unknown face
                cv2.putText(frame, "Unknown", (x, y-40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                if "Unknown" not in tracked_faces.values():
                    tracked_faces["Unknown"] = (x, y, w, h)  # Add to tracked faces

        # Detect left profile faces
        left_faces = left_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in left_faces:
            serial, conf = recognizer.predict(gray[y:y+h, x:x+w])
            if conf < 50:
                name = name_list[serial]
                matric_number, department_name = student_info.get(name, ("Unknown", "Unknown"))
                add_student_record(name, matric_number, department_name)
                if serial not in tracked_faces:  # If face not tracked yet
                    tracked_faces[serial] = (x, y, w, h)  # Add to tracked faces
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (50, 255, 50), 1)
                    cv2.putText(frame, name, (x, y-40), cv2.FONT_HERSHEY_SIMPLEX, 1, (50, 255, 50), 2)
            else:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 1)  # Red rectangle for unknown face
                cv2.putText(frame, "Unknown", (x, y-40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                if "Unknown" not in tracked_faces.values():
                    tracked_faces["Unknown"] = (x, y, w, h)  # Add to tracked faces

        # Detect right profile faces
        right_faces = right_cascade.detectMultiScale(cv2.flip(gray, 1), 1.3, 5)
        for (x, y, w, h) in right_faces:
            x = gray.shape[1] - x - w
            serial, conf = recognizer.predict(gray[y:y+h, x:x+w])
            if conf < 50:
                name = name_list[serial]
                matric_number, department_name = student_info.get(name, ("Unknown", "Unknown"))
                add_student_record(name, matric_number, department_name)
                if serial not in tracked_faces:  # If face not tracked yet
                    tracked_faces[serial] = (x, y, w, h)  # Add to tracked faces
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 50, 50), 1)
                    cv2.putText(frame, name, (x, y-40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 50, 50), 2)
            else:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 1)  # Red rectangle for unknown face
                cv2.putText(frame, "Unknown", (x, y-40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                if "Unknown" not in tracked_faces.values():
                    tracked_faces["Unknown"] = (x, y, w, h)  # Add to tracked faces

        cv2.imshow("Frame", frame)
        k = cv2.waitKey(1)  # Capture key press event
        if k == ord('q') or k == 27:  # Check if 'q' or ESC key is pressed
            break

    opencv_window_closed = True
    video.release()
    cv2.destroyAllWindows()


# Initialize opencv_window_closed before starting the face recognition thread
opencv_window_closed = False
threading.Thread(target=face_recognition, daemon=True).start()

create_database_table_and_save_as_pdf(host="localhost", user="root", password="Immun0calypse", database="Attendancedb")
display_table_in_app()
