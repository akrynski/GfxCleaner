import os
from PIL import Image
import sqlite3
import hashlib
import shutil
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()  # Hide the main window


# Function to scan the specified media for image files
def scan_media_for_images(media_path):
    image_files = []
    for root, dirs, files in os.walk(media_path):
        for file in files:
            if file.lower().endswith(('.tiff', '.jpeg', '.jpg', '.png','.cr2','.bmp')):
                image_files.append(os.path.join(root, file))
    return image_files


# Function to create an SQLite database and store image file information
def create_image_database(image_files):
    conn = sqlite3.connect('image_database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS images
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, file_path TEXT, checksum TEXT)''')

    for file_path in image_files:
        with open(file_path, 'rb') as f:
            checksum = hashlib.md5(f.read()).hexdigest()
        c.execute("INSERT INTO images (file_path, checksum) VALUES (?, ?)", (file_path, checksum))

    conn.commit()
    conn.close()


# Function to display and manage duplicates
def display_and_manage_duplicates():
    conn = sqlite3.connect('image_database.db')
    c = conn.cursor()
    c.execute('''SELECT file_path, checksum, COUNT(*) AS count
                  FROM images
                  GROUP BY checksum
                  HAVING count > 1''')
    duplicates = c.fetchall()

    # Display duplicates to the user and manage them
    # User input and decision making can be implemented here
    for duplicate in duplicates:
        print("Duplicate File:", duplicate[0])

    conn.close()


# Function to move files to the new storage location
def move_files_to_new_location(new_storage_location):
    conn = sqlite3.connect('image_database.db')
    c = conn.cursor()
    c.execute("SELECT file_path FROM images")
    files_to_move = c.fetchall()

    for file_path in files_to_move:
        shutil.move(file_path[0], new_storage_location)

    conn.close()


# Dialog for a path
def open_dialog():
    file_path = filedialog.askdirectory()  # Open a file dialog to select a file

    print("Selected file path:", file_path)
    return file_path


scan_folder = open_dialog()
my_images = scan_media_for_images(scan_folder)

create_image_database(my_images)
display_and_manage_duplicates()

new_location = open_dialog()
move_files_to_new_location(new_location)
