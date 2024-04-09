import tkinter as tk
from tkinter import filedialog

def upload_file():
    file_path = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
    if file_path:
        print("Selected file:", file_path)
        # You can perform further operations with the selected file here

def show_window():
    # Create a Tkinter window
    window = tk.Tk()
    window.geometry("400x200")
    window.title("File Uploader")
    window.iconbitmap("check.ico")

    label_text = "Upload Your Model as a '.zip' file, close to use default model"
    label = tk.Label(window, text=label_text, wraplength=300)
    label.pack(pady=10)

    # Create a button for uploading a file
    upload_button = tk.Button(window, text="Upload File", command=upload_file)
    upload_button.pack(pady=20)

    # Start the Tkinter event loop
    window.mainloop()

if __name__ == "__main__":
    show_window()
