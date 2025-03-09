import gi
import logging
import os
import asyncio
import subprocess
import aiohttp
from collections import deque

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GdkPixbuf

WALLHAVEN_API_KEY = "YOUR_API_KEY"
WALLHAVEN_URL = "https://wallhaven.cc/api/v1/search"

class WallpaperSelectorWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Wallpaper Selector")
        self.set_default_size(800, 600)

        # Main container
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.box)

        # Categories drop list
        self.category_combo = Gtk.ComboBoxText()
        self.category_combo.append_text("general")
        self.category_combo.append_text("anime")
        self.category_combo.append_text("people")
        self.category_combo.set_active(0)
        self.category_combo.connect("changed", self.on_category_changed)
        self.box.pack_start(self.category_combo, False, False, 0)

        # Filters
        self.resolution_combo = Gtk.ComboBoxText()
        self.resolution_combo.append_text("Any")
        self.resolution_combo.append_text("1920x1080")
        self.resolution_combo.append_text("2560x1440")
        self.resolution_combo.append_text("3840x2160")
        self.resolution_combo.set_active(0)
        self.resolution_combo.connect("changed", self.on_category_changed)
        self.box.pack_start(self.resolution_combo, False, False, 0)

        self.sorting_combo = Gtk.ComboBoxText()
        self.sorting_combo.append_text("Toplist")
        self.sorting_combo.append_text("Latest")
        self.sorting_combo.append_text("Random")
        self.sorting_combo.set_active(0)
        self.sorting_combo.connect("changed", self.on_category_changed)
        self.box.pack_start(self.sorting_combo, False, False, 0)

        # Grid with images
        self.grid = Gtk.FlowBox()
        self.grid.set_valign(Gtk.Align.START)
        self.grid.set_max_children_per_line(4)
        self.grid.set_selection_mode(Gtk.SelectionMode.NONE)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add(self.grid)

        self.box.pack_start(scrolled_window, True, True, 0)

        # Set Wallpaper
        self.set_button = Gtk.Button(label="Set as Wallpaper")
        self.set_button.connect("clicked", self.on_set_wallpaper)
        self.box.pack_start(self.set_button, False, False, 0)

        # Wallpaper history
        self.history = deque(maxlen=10)

        self.selected_image = None
        self.selected_full_image = None

        asyncio.run(self.load_images())

        self.show_all()

    async def load_images(self):
        self.grid.foreach(lambda widget: self.grid.remove(widget))

        category = self.get_current_category()
        resolution = self.get_current_resolution()
        sorting = self.get_current_sorting()

        logging.info(f"Loading images for category: {category}, resolution: {resolution}, sorting: {sorting}")

        params = {
            "apikey": WALLHAVEN_API_KEY,
            "q": category,
            "sorting": sorting.lower(),
            "categories": "111",
            "purity": "100",
            "atleast": resolution if resolution != "Any" else ""
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(WALLHAVEN_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    for wallpaper in data.get('data', []):
                        try:
                            thumb_url = wallpaper.get('thumbs', {}).get('small')
                            full_url = wallpaper.get('path')
                            if thumb_url and full_url:
                                await self.add_image_from_url(thumb_url, full_url)
                        except Exception as e:
                            logging.warning(f"Failed to load image: {e}")
                else:
                    logging.error(f"Failed to fetch data: {response.status}")

        self.grid.show_all()

    async def add_image_from_url(self, thumb_url, full_url):
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as response:
                if response.status == 200:
                    buffer = await response.read()
                    loader = GdkPixbuf.PixbufLoader.new()
                    loader.write(buffer)
                    loader.close()
                    pixbuf = loader.get_pixbuf()

                    image = Gtk.Image.new_from_pixbuf(pixbuf)
                    image.set_tooltip_text(full_url)
                    image_event = Gtk.EventBox()
                    image_event.add(image)
                    image_event.connect("button-press-event", self.on_image_selected, full_url)
                    self.grid.add(image_event)

    def get_current_category(self):
        return self.category_combo.get_active_text()

    def get_current_resolution(self):
        return self.resolution_combo.get_active_text()

    def get_current_sorting(self):
        return self.sorting_combo.get_active_text()

    def on_category_changed(self, combo):
        asyncio.run(self.load_images())

    def on_image_selected(self, widget, event, full_url):
        logging.info(f"Selected image: {full_url}")
        self.selected_image = full_url

    async def download_image(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    file_path = "/tmp/wallpaper.jpg"
                    with open(file_path, "wb") as f:
                        f.write(image_data)
                    return file_path
                else:
                    logging.error(f"Failed to download image: {response.status}")
                    return None

    def on_set_wallpaper(self, button):
        if not self.selected_image:
            logging.warning("No image selected")
            return

        logging.info(f"Downloading wallpaper: {self.selected_image}")

        asyncio.run(self.apply_wallpaper())

    async def apply_wallpaper(self):
        file_path = await self.download_image(self.selected_image)
        if not file_path:
            logging.error("Failed to download image")
            return

        self.history.append(self.selected_image)
        logging.info(f"Wallpaper history: {list(self.history)}")

        try:
            subprocess.run([
                "gsettings", "set", "org.gnome.desktop.background", "picture-uri", f"file://{file_path}"
            ], check=True)
            logging.info("Wallpaper set successfully!")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to set wallpaper: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = Gtk.Application(application_id="org.example.WallpaperSelector")

    def on_activate(app):
        win = WallpaperSelectorWindow(app)
        win.show_all()

    app.connect("activate", on_activate)
    app.run(None)
