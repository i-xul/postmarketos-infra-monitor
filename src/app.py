#!/usr/bin/env python3

import json
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


class InfraMonitor(Gtk.Window):
    def __init__(self):
        super().__init__(title="postmarketOS Infra Monitor")

        self.devices = [
            self.load_device("raspi5.json"),
            self.load_device("raspi4.json"),
        ]
        self.current_index = 0

        self.touch_start_x = None
        self.touch_end_x = None

        self.set_default_size(800, 480)
        self.set_border_width(20)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.add(self.main_box)

        self.title_label = Gtk.Label()
        self.title_label.set_xalign(0)

        self.cards_grid = Gtk.Grid()
        self.cards_grid.set_row_spacing(12)
        self.cards_grid.set_column_spacing(12)

        self.nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        self.prev_button = Gtk.Button(label="← Previous")
        self.next_button = Gtk.Button(label="Next →")

        self.prev_button.connect("clicked", self.previous_device)
        self.next_button.connect("clicked", self.next_device)

        self.nav_box.pack_start(self.prev_button, True, True, 0)
        self.nav_box.pack_start(self.next_button, True, True, 0)

        self.main_box.pack_start(self.title_label, False, False, 0)
        self.main_box.pack_start(self.cards_grid, True, True, 0)
        self.main_box.pack_start(self.nav_box, False, False, 0)

        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK
        )

        self.connect("button-press-event", self.on_touch_press)
        self.connect("button-release-event", self.on_touch_release)
        self.connect("key-press-event", self.on_key_press)

        self.load_css()
        self.render_device()

    def load_device(self, filename):
        with open(DATA_DIR / filename, "r", encoding="utf-8") as file:
            return json.load(file)

    def create_card(self, title, value):
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.NONE)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(14)

        title_label = Gtk.Label()
        title_label.set_markup(f"<span size='12000' weight='bold'>{title}</span>")
        title_label.set_xalign(0)

        value_label = Gtk.Label()
        value_label.set_markup(f"<span size='22000' weight='bold'>{value}</span>")
        value_label.set_xalign(0)

        box.pack_start(title_label, False, False, 0)
        box.pack_start(value_label, True, True, 0)

        frame.add(box)
        frame.get_style_context().add_class("metric-card")

        return frame

    def clear_grid(self):
        for child in self.cards_grid.get_children():
            self.cards_grid.remove(child)

    def render_device(self):
        device = self.devices[self.current_index]
        fail2ban = device.get("fail2ban", {})

        self.title_label.set_markup(
            f"<span size='26000' weight='bold'>{device['name']}</span>\n"
            f"<span size='13000'>{device['hostname']}</span>"
        )

        self.clear_grid()

        cards = [
            self.create_card("CPU TEMP", f"{device['cpu_temp']} °C"),
            self.create_card("CPU LOAD", f"{device['cpu_load']} %"),
            self.create_card("RAM", f"{device['ram_used']} / {device['ram_total']} GB"),
            self.create_card("UPTIME", device["uptime"]),
            self.create_card("FAIL2BAN", f"{fail2ban.get('total_bans', 'n/a')} bans"),
            self.create_card("LAST BANNED IP", fail2ban.get("last_banned_ip", "n/a")),
        ]

        positions = [
            (0, 0), (1, 0),
            (0, 1), (1, 1),
            (0, 2), (1, 2),
        ]

        for card, (column, row) in zip(cards, positions):
            self.cards_grid.attach(card, column, row, 1, 1)

        self.cards_grid.show_all()

    def previous_device(self, button=None):
        if self.current_index > 0:
            self.current_index -= 1
            self.render_device()

    def next_device(self, button=None):
        if self.current_index < len(self.devices) - 1:
            self.current_index += 1
            self.render_device()

    def on_touch_press(self, widget, event):
        self.touch_start_x = event.x

    def on_touch_release(self, widget, event):
        self.touch_end_x = event.x

        if self.touch_start_x is None or self.touch_end_x is None:
            return

        delta_x = self.touch_end_x - self.touch_start_x
        swipe_threshold = 80

        if delta_x > swipe_threshold:
            self.previous_device()
        elif delta_x < -swipe_threshold:
            self.next_device()

        self.touch_start_x = None
        self.touch_end_x = None

    def on_key_press(self, widget, event):
        key = Gdk.keyval_name(event.keyval)

        if key == "Right":
            self.next_device()
        elif key == "Left":
            self.previous_device()
        elif key == "Escape":
            Gtk.main_quit()

    def load_css(self):
        css = b"""
        window {
            background-color: #111111;
            color: #eeeeee;
        }

        label {
            color: #eeeeee;
        }

        button {
            font-size: 18px;
            padding: 10px;
        }

        .metric-card {
            background-color: #222222;
            border-radius: 14px;
            border: 1px solid #444444;
        }
        """

        provider = Gtk.CssProvider()
        provider.load_from_data(css)

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )


def main():
    app = InfraMonitor()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
