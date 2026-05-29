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
        self.set_border_width(24)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        self.add(self.main_box)

        self.title_label = Gtk.Label()
        self.title_label.set_xalign(0)

        self.metrics_label = Gtk.Label()
        self.metrics_label.set_xalign(0)
        self.metrics_label.set_yalign(0)

        self.nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        self.prev_button = Gtk.Button(label="← Previous")
        self.next_button = Gtk.Button(label="Next →")

        self.prev_button.connect("clicked", self.previous_device)
        self.next_button.connect("clicked", self.next_device)

        self.nav_box.pack_start(self.prev_button, True, True, 0)
        self.nav_box.pack_start(self.next_button, True, True, 0)

        self.main_box.pack_start(self.title_label, False, False, 0)
        self.main_box.pack_start(self.metrics_label, True, True, 0)
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

    def render_device(self):
        device = self.devices[self.current_index]
        fail2ban = device.get("fail2ban", {})

        self.title_label.set_markup(
            f"<span size='28000' weight='bold'>{device['name']}</span>\n"
            f"<span size='14000'>{device['hostname']}</span>"
        )

        text = (
            f"CPU temperature: {device['cpu_temp']} °C\n"
            f"CPU load:        {device['cpu_load']} %\n"
            f"RAM:             {device['ram_used']} / {device['ram_total']} GB\n"
            f"Uptime:          {device['uptime']}\n\n"
            f"Fail2ban bans:   {fail2ban.get('total_bans', 'n/a')}\n"
            f"Last banned IP:  {fail2ban.get('last_banned_ip', 'n/a')}"
        )

        self.metrics_label.set_markup(
            f"<span size='18000'><tt>{text}</tt></span>"
        )

    def previous_device(self, button=None):
        self.current_index = (self.current_index - 1) % len(self.devices)
        self.render_device()

    def next_device(self, button=None):
        self.current_index = (self.current_index + 1) % len(self.devices)
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
            font-size: 20px;
            padding: 12px;
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
