import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
from PIL import Image, ImageDraw, ImageFont
import cv2
import os
import fcntl

lock_file_path = "app_lock.lock"

def acquire_lock():
    try:
        lock_file = open(lock_file_path, 'w')
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_file
    except IOError:
        return None

def release_lock(lock_file):
    try:
        fcntl.flock(lock_file, fcntl.LOCK_UN)
        lock_file.close()
        os.remove(lock_file_path)
    except Exception as e:
        print(f"Error releasing lock: {e}")

class FileSelectorWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Pekman analyzer")
        self.set_window_properties()

        label = tk.Label(self, text="Select the file type")
        label.pack(side="top", pady=20)

        self.choice = tk.IntVar()

        image_radio = tk.Radiobutton(self, text="Image", variable=self.choice, value=1)
        image_radio.pack()

        video_radio = tk.Radiobutton(self, text="Video", variable=self.choice, value=2)
        video_radio.pack()

        next_button = tk.Button(self, text="Next", command=self.open_next_window)
        next_button.pack(side="bottom", pady=10, padx=10, anchor="se")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.master.destroy()

    def set_window_properties(self):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x_position = (screen_width - 400) // 2
        y_position = (screen_height - 300) // 2
        self.geometry(f"400x300+{x_position}+{y_position}")

    def open_next_window(self):
        choice = self.choice.get()
        if choice == 1:
            OpenImageWindow(root)
            self.destroy()
        elif choice == 2:
            OpenVideoWindow(root)
            self.destroy()



class ProgressWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Pekman analyzer")
        self.set_window_properties()

        self.progress_label = tk.Label(self, text="Processing...")
        self.progress_label.pack(side="top", pady=20)

        self.progress_bar = ttk.Progressbar(self, length=200, mode="indeterminate")
        self.progress_bar.pack(pady=10)
        self.progress_bar.start()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.master.destroy()

    def set_window_properties(self):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x_position = (screen_width - 400) // 2
        y_position = (screen_height - 300) // 2
        self.geometry(f"400x300+{x_position}+{y_position}")


class OpenVideoWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Pekman analyzer")
        self.set_window_properties()

        self.progress_window = None

        upload_button = tk.Button(self, text="Upload Video", command=lambda: self.upload_file("video"))
        upload_button.pack(side="top", pady=20)

        next_button = tk.Button(self, text="Next", state=tk.DISABLED, command=lambda: self.process_file("video"))
        next_button.pack(side="right", padx=10, anchor="se")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        back_button = tk.Button(self, text="Back", command=self.on_back)
        back_button.pack(side="left", padx=10, anchor="sw")

    def on_close(self):
        self.master.destroy()

    def set_window_properties(self):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x_position = (screen_width - 400) // 2
        y_position = (screen_height - 300) // 2
        self.geometry(f"400x300+{x_position}+{y_position}")

    def upload_file(self, file_type):
        file_path = filedialog.askopenfilename()

        if file_path:
            if not file_path.lower().endswith(('.mp4', '.avi', '.mov')):
                messagebox.showerror("Error", "Upload only videos!")
                return
            if self.file_size(file_path) > 100:
                messagebox.showerror("Error", "The maximum video size should be less than 100 MB.")
            else:
                self.update_upload_button(file_path, file_type)
                self.update_next_button(file_path, file_type)

    def file_size(self, file_path):
        return os.path.getsize(file_path) / (1024 * 1024)

    def process_file(self, file_type):
        new_path = self.get_new_path()
        if new_path:
            self.progress_window = ProgressWindow(self.master)
            thread = threading.Thread(target=self.run_main_script, args=(new_path,))
            thread.start()
            self.destroy()

    def run_main_script(self, new_path):
        if new_path:
            from processing import processing_file
            result = processing_file(new_path)
            self.progress_window.destroy()
            self.display_results_window(result, new_path)

    def display_results_window(self, result, new_path):
        results_window = ResultsWindow(self.master, result, new_path)

    def get_new_path(self):
        upload_button = [widget for widget in self.winfo_children() if isinstance(widget, tk.Button)][0]
        return upload_button.cget("text").split("\n")[-1]

    def update_upload_button(self, file_path, file_type):
        upload_button = [widget for widget in self.winfo_children() if isinstance(widget, tk.Button)][0]
        upload_button.config(state=tk.DISABLED, text="The file has already been uploaded\n{}".format(file_path))

    def update_next_button(self, file_path, file_type):
        next_button = [widget for widget in self.winfo_children() if
                       isinstance(widget, tk.Button) and "Next" in widget.cget("text")][0]
        next_button.config(state=tk.NORMAL, command=lambda: self.process_file(file_type))

    def on_back(self):
        FileSelectorWindow(self.master)
        self.after(800, self.destroy)


class OpenImageWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Pekman analyzer")
        self.set_window_properties()

        self.progress_window = None

        upload_button = tk.Button(self, text="Upload Image", command=lambda: self.upload_file("image"))
        upload_button.pack(side="top", pady=20)

        next_button = tk.Button(self, text="Next", state=tk.DISABLED, command=lambda: self.process_file("image"))
        next_button.pack(side="right", padx=10, anchor="se")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        back_button = tk.Button(self, text="Back", command=self.on_back)
        back_button.pack(side="left", padx=10, anchor="sw")

    def on_close(self):
        self.master.destroy()

    def set_window_properties(self):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x_position = (screen_width - 400) // 2
        y_position = (screen_height - 300) // 2
        self.geometry(f"400x300+{x_position}+{y_position}")

    def upload_file(self, file_type):
        file_path = filedialog.askopenfilename()

        if file_path:
            if not file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                messagebox.showerror("Error", "Only upload images!")
                return
            if self.file_size(file_path) > 10:
                messagebox.showerror("Error", "The maximum image size should be less than 10 MB.")
            else:
                self.update_upload_button(file_path, file_type)
                self.update_next_button(file_path, file_type)

    def file_size(self, file_path):
        return os.path.getsize(file_path) / (1024 * 1024)

    def process_file(self, file_type):
        new_path = self.get_new_path()
        if new_path:
            self.progress_window = ProgressWindow(self.master)
            thread = threading.Thread(target=self.run_main_script, args=(new_path,))
            thread.start()
            self.destroy()

    def run_main_script(self, new_path):
        if new_path:
            from processing import processing_file
            result = processing_file(new_path)
            self.progress_window.destroy()
            self.display_results_window(result, new_path)

    def display_results_window(self, result, new_path):
        results_window = ResultsWindow(self.master, result, new_path)

    def get_new_path(self):
        upload_button = [widget for widget in self.winfo_children() if isinstance(widget, tk.Button)][0]
        return upload_button.cget("text").split("\n")[-1]

    def update_upload_button(self, file_path, file_type):
        upload_button = [widget for widget in self.winfo_children() if isinstance(widget, tk.Button)][0]
        upload_button.config(state=tk.DISABLED, text="The file has already been uploaded\n{}".format(file_path))

    def update_next_button(self, file_path, file_type):
        next_button = [widget for widget in self.winfo_children() if
                       isinstance(widget, tk.Button) and "Next" in widget.cget("text")][0]
        next_button.config(state=tk.NORMAL, command=lambda: self.process_file(file_type))

    def on_back(self):
        FileSelectorWindow(self.master)
        self.after(800, self.destroy)


class ResultsWindow(tk.Toplevel):
    def __init__(self, master, result, new_path):
        super().__init__(master)
        self.title("Pekman analyzer")
        self.set_window_properties()

        view_result_button = tk.Button(self, text="View Result", command=lambda: self.view_result(new_path, result))
        view_result_button.pack(side="top", pady=20)

        save_result_button = tk.Button(self, text="Save Result", command=lambda: self.save_result(new_path, result))
        save_result_button.pack(pady=10)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        back_button = tk.Button(self, text="Back", command=self.on_back)
        back_button.pack(side="left", padx=10, anchor="sw")

    def on_close(self):
        self.master.destroy()

    def set_window_properties(self):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x_position = (screen_width - 400) // 2
        y_position = (screen_height - 300) // 2
        self.geometry(f"400x300+{x_position}+{y_position}")

    def on_back(self):
        FileSelectorWindow(self.master)
        self.after(800, self.destroy)

    def view_result(self, new_path, result):
        if isinstance(result, str):
            img = Image.open(new_path)
            draw = ImageDraw.Draw(img)

            img_width, img_height = img.size

            font_size = max(1, int(img_width / 25))

            font = ImageFont.load_default().font_variant(size=font_size)

            text_color = 255

            draw.text((10, 10), result, text_color, font=font)

            img.show()

        elif isinstance(result, list):
            for frame in result:
                cv2.imshow('Processed Video', frame)
                if cv2.waitKey(30) & 0xFF == 27:  # Pressing 'Esc' to exit
                    break

            cv2.destroyAllWindows()

    def save_result(self, new_path, result):
        if isinstance(result, str):
            img = Image.open(new_path)
            draw = ImageDraw.Draw(img)

            img_width, img_height = img.size

            font_size = max(1, int(img_width / 25))

            font = ImageFont.load_default().font_variant(size=font_size)

            text_color = 255

            draw.text((10, 10), result, text_color, font=font)
            save_path = filedialog.asksaveasfilename(defaultextension=".jpeg",
                                                       filetypes=[("JPEG files", "*.jpg"), ("All files", "*.*")])
            if save_path:
                img.save(save_path)
        elif isinstance(result, list):
            save_path = filedialog.asksaveasfilename(defaultextension=".mp4",
                                                      filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")])
            if save_path:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                height, width, _ = result[0].shape
                video_writer = cv2.VideoWriter(save_path, fourcc, 30.0, (width, height))

                for frame in result:
                    video_writer.write(frame)

                video_writer.release()

def main():
    global root
    root = tk.Tk()
    root.withdraw()
    root.protocol("WM_DELETE_WINDOW", on_main_window_close)
    FileSelectorWindow(root)
    root.mainloop()

def on_main_window_close():
    root.destroy()
    for window in root.winfo_children():
        if isinstance(window, tk.Toplevel):
            window.destroy()


if __name__ == "__main__":
    main()
