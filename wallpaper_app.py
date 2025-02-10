import os
import ctypes
import pywin

def set_wallpaper(image_path):
    """Set the wallpaper to the specified image path."""
    SPI_SETDESKWALLPAPER = 20
    ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path , 0)

def load_images_from_directory(directory):
    """Load images from a directory and return their paths."""
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    images = [os.path.join(directory, f) for f in os.listdir(directory) if
os.path.isfile(os.path.join(directory, f)) and os.path.splitext(f)[1].lower() in
valid_extensions]
    return images

def next_wallpaper():
    """Change to the next wallpaper."""
    global current_image_index
    current_image_index = (current_image_index + 1) % len(images)
    set_wallpaper(images[current_image_index])
    update_label()

def previous_wallpaper():
    """Change to the previous wallpaper."""
    global current_image_index
    current_image_index = (current_image_index - 1) % len(images)
    set_wallpaper(images[current_image_index])
    update_label()

def choose_directory():
    """Choose a directory and load images from it."""
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()  # Hide the main window
    directory = filedialog.askdirectory()
    root.destroy()

    if directory:
        global images, current_image_index
        images = load_images_from_directory(directory)
        if images:
            current_image_index = 0
            set_wallpaper(images[current_image_index])
            update_label()
        else:
            messagebox.showwarning("No Images", "No valid images found in the selected directory.")

def update_label():
    """Update the label to show the current image name."""
    if images and current_image_index < len(images):
        label.config(text=os.path.basename(images[current_image_index]))

def create_tray_icon():
    """Create a system tray icon with options to change wallpapers."""
    import pystray
    from PIL import Image, ImageDraw

    # Create an icon image (24x24 pixels)
    image = Image.new('RGBA', (24, 24), "black")
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, 23, 23), fill="white", outline="gray")

    def on_quit(icon, item):
        icon.stop()
        root.destroy()

    menu = (
        pystray.MenuItem('Next Wallpaper', lambda: next_wallpaper()),
        pystray.MenuItem('Previous Wallpaper', lambda: previous_wallpaper()),
        pystray.MenuItem('Exit', on_quit),
    )

    return pystray.Icon("Wallpaper Changer", image, "Wallpaper Changer", menu)

if __name__ == "__main__":
    # Create or open a named mutex
    import win32event
    mutex_name = "WallpaperChangerMutex"
    mutex = win32event.CreateMutex(None, True, mutex_name)
    if win32api.GetLastError() == win32con.ERROR_ALREADY_EXISTS:
        messagebox.showerror("Error", "Another instance of this application is already running.")
        exit()

    import tkinter as tk
    from tkinter import messagebox

    # Main application setup
    root = tk.Tk()
    root.title("Wallpaper Changer")
    root.geometry("300x200")

    frame = tk.Frame(root)
    frame.pack(pady=20)

    global label, images, current_image_index
    label = tk.Label(frame, text="No image selected", font=('Helvetica', 14))
    label.pack(pady=10)

    choose_button = tk.Button(frame, text="Choose Directory", command=choose_directory)
    choose_button.pack()

    next_button = tk.Button(frame, text="Next Wallpaper", command=next_wallpaper)
    next_button.pack(side=tk.LEFT, padx=5)

    prev_button = tk.Button(frame, text="Previous Wallpaper", command=previous_wallpaper)
    prev_button.pack(side=tk.RIGHT, padx=5)

    about_button = tk.Button(frame, text="About", command=lambda: messagebox.showinfo("About",
"Wallpaper Changer by Alexander Rozov\nVersion 1.0"))
    about_button.pack(pady=10)

    images = []
    current_image_index = 0

    # Create tray icon
    tray_icon = create_tray_icon()

    def on_closing():
        """Handle the window close event."""
        root.withdraw()
        tray_icon.run_detached()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()