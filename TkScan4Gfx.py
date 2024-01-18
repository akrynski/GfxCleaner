import hashlib
import os
import shutil
import sqlite3
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()  # Hide the main window


# Funkcja do skanowania plików na określonym nośniku
def scan_media_for_images(media_path):
    image_files = []
    for root, dirs, files in os.walk(media_path):
        for file in files:
            if file.lower().endswith(('.tiff', '.jpeg', '.jpg', '.png', '.cr2', '.bmp')):
                image_files.append(os.path.join(root, file))
    return image_files


# Funkcja do obliczania sumy kontrolnej pliku
def calculate_checksum(file_path):
    with open(file_path, 'rb') as f:
        checksum = hashlib.md5(f.read()).hexdigest()
    return checksum


# Funkcja do tworzenia bazy danych SQLite i zapisywania informacji o plikach
def create_image_database(image_files, database_path):
    conn = sqlite3.connect(database_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS images
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, file_path TEXT, checksum TEXT, destination_dir TEXT)''')

    for file_path in image_files:
        checksum = calculate_checksum(file_path)
        # czy istnieje już w bazie?
        c.execute("SELECT COUNT(*) FROM images WHERE checksum=?", (checksum,))
        result = c.fetchone()
        if result[0] > 0:
            # tak - aktualizuj lokalizację
            c.execute("UPDATE images SET file_path=? WHERE checksum=?", (file_path, checksum))
        else:
            # nie - dodaj nowy rekord
            c.execute("INSERT INTO images (file_path, checksum) VALUES (?, ?)", (file_path, checksum))
    try:
        conn.commit()
    except sqlite3.Error as er:
        print('SQLite error: %s' % (' '.join(er.args)))
        print("Exception class is: ", er.__class__)
        print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(traceback.format_exception(exc_type, exc_value, exc_tb))
    conn.close()


# Funkcja do wykrywania duplikatów i flagowania ich w bazie danych
def flag_duplicates_in_database(database_path):
    conn = sqlite3.connect(database_path)
    c = conn.cursor()
    c.execute('''SELECT checksum, COUNT(*) AS count
                 FROM images
                 GROUP BY checksum
                 HAVING count > 1''')
    duplicates = c.fetchall()

    with open('duplikaty.log', 'w') as log_file:
        for duplicate in duplicates:
            c.execute("SELECT id, file_path FROM images WHERE checksum=?", (duplicate[0],))
            duplicate_files = c.fetchall()
            for i, file_info in enumerate(duplicate_files):
                if i > 0:
                    log_file.write(f"Duplicate File: {file_info[1]}\n")
                    c.execute("UPDATE images SET destination_dir = ? WHERE id = ?", ('duplicate', file_info[0]))

    conn.commit()
    conn.close()


# Funkcja do przenoszenia plików do nowej lokalizacji i aktualizacji bazy danych
def move_files_to_new_location(database_path, new_storage_location):
    conn = sqlite3.connect(database_path)
    c = conn.cursor()
    c.execute("SELECT id, file_path FROM images WHERE destination_dir IS NULL")
    files_to_move = c.fetchall()

    for file_info in files_to_move:
        file_id, file_path = file_info
        new_file_path = os.path.join(new_storage_location, os.path.basename(file_path))
        try:
            shutil.move(file_path, new_file_path)
            c.execute("UPDATE images SET destination_dir = ? WHERE id = ?", (new_storage_location, file_id))
        except Exception as e:
            with open('duplikaty.log', 'a') as log_file:
                log_file.write(f"Error moving file: {file_path} - {str(e)}\n")

    conn.commit()
    conn.close()


# Dialog for a path
def open_dialog(title):
    file_path = filedialog.askdirectory(title=title)  # Open a file dialog to select a file
    print("Selected file path:", file_path)
    return file_path


def restore_files_to_original_location(database_path):
    conn = sqlite3.connect(database_path)
    c = conn.cursor()

    c.execute("SELECT id, file_path, destination_dir FROM images WHERE destination_dir IS NOT NULL")
    files_to_restore = c.fetchall()

    for file_info in files_to_restore:
        file_id, file_path, destination_dir = file_info
        file_path=os.path.normpath(file_path).replace('\\', '/')
        file_name = os.path.basename(file_path)
        dir_name = os.path.dirname(file_path)
        try:
            shutil.move(destination_dir+"\\"+file_name, dir_name)
            c.execute("UPDATE images SET destination_dir = NULL WHERE id = ?", (file_id,))
        except Exception as e:
            print(f"Error restoring file: {file_path} - {str(e)}")

    conn.commit()
    conn.close()


# Przykładowe użycie


# Główna część programu
'''
media_path = open_dialog('Wskaż gdzie szukać zdjęć.')
database_path = 'image_database.db'
new_storage_location = open_dialog('Wskaż gdzie zapisać zdjęcia.')

image_files = scan_media_for_images(media_path)
create_image_database(image_files, database_path)
flag_duplicates_in_database(database_path)
move_files_to_new_location(database_path, new_storage_location)
'''
database_path = 'image_database.db'
restore_files_to_original_location(database_path)
