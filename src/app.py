#!/usr/bin/env python3

import json
from datetime import datetime
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

from telemetry import collect_all_devices


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REFRESH_INTERVAL_SECONDS = 30


class InfraMonitor(Gtk.Window):
    def __init__(self):
        super().__init__(title="postmarketOS Infra Monitor")

        self.last_refresh_time = None
        self.devices = self.load_devices()
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

        self.refresh_label = Gtk.Label()
        self.refresh_label.set_xalign(0.5)

        self.nav_box.pack_start(self.prev_button, True, True, 0)
        self.nav_box.pack_start(self.refresh_label, True, True, 0)
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

        GLib.timeout_add_seconds(
            REFRESH_INTERVAL_SECONDS,
            self.refresh_devices
        )

    def load_devices(self):
        try:
            devices = collect_all_devices()
            self.last_refresh_time = datetime.now()

            if devices:
                return devices

        except Exception as error:
            print(f"Live telemetry failed, using fallback JSON data: {error}")

        self.last_refresh_time = datetime.now()

        return [
            self.load_device_from_json("raspi5.json"),
            self.load_device_from_json("raspi4.json"),
        ]

    def load_device_from_json(self, filename):
        with open(DATA_DIR / filename, "r", encoding="utf-8") as file:
            return json.load(file)

    def refresh_devices(self):
        previous_device_name = None

        if self.devices and self.current_index < len(self.devices):
            previous_device_name = self.devices[self.current_index].get("name")

        self.devices = self.load_devices()

        if previous_device_name:
            for index, device in enumerate(self.devices):
                if device.get("name") == previous_device_name:
                    self.current_index = index
                    break
            else:
                self.current_index = 0

        if self.current_index >= len(self.devices):
            self.current_index = max(0, len(self.devices) - 1)

        self.render_device()

        return True

    def create_card(self, title, value, card_class="metric-card"):
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.NONE)

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=6
        )
        box.set_border_width(14)

        title_label = Gtk.Label()
        title_label.set_markup(
            f"<span size='12000' weight='bold'>{title}</span>"
        )
        title_label.set_xalign(0)

        value_label = Gtk.Label()
        value_label.set_markup(
            f"<span size='20000' weight='bold'>{value}</span>"
        )
        value_label.set_xalign(0)
        value_label.set_line_wrap(True)

        box.pack_start(title_label, False, False, 0)
        box.pack_start(value_label, True, True, 0)

        frame.add(box)

        frame.get_style_context().add_class(card_class)

        return frame

    def clear_grid(self):
        for child in self.cards_grid.get_children():
            self.cards_grid.remove(child)

    def render_device(self):
        if not self.devices:
            return

        device = self.devices[self.current_index]

        self.clear_grid()

        if device.get("offline"):
            self.render_offline_device(device)
        else:
            self.render_online_device(device)

        self.update_navigation_buttons()
        self.update_refresh_label()
        self.cards_grid.show_all()

    def render_online_device(self, device):
        pihole = device.get("pihole", {})

        self.title_label.set_markup(
            f"<span size='26000' weight='bold'>{device['name']}</span>\n"
            f"<span size='13000'>{device['hostname']}</span>"
        )

        if pihole.get("enabled"):
            cards = self.build_pihole_cards(device)
        else:
            cards = self.build_default_cards(device)

        self.attach_cards(cards)

    def build_default_cards(self, device):
        fail2ban = device.get("fail2ban", {})
        fail2ban_text = self.format_fail2ban_text(fail2ban)

        return [
            self.create_card("CPU TEMP", f"{device['cpu_temp']} °C"),
            self.create_card("CPU LOAD", str(device["cpu_load"])),
            self.create_card("RAM", f"{device['ram_used']} / {device['ram_total']} GB"),
            self.create_card("UPTIME", device["uptime"]),
            self.create_card("FAIL2BAN", fail2ban_text),
            self.create_card("HOST", device["hostname"]),
        ]

    def build_pihole_cards(self, device):
        pihole = device.get("pihole", {})

        return [
            self.create_card("CPU TEMP", f"{device['cpu_temp']} °C"),
            self.create_card("RAM", f"{device['ram_used']} / {device['ram_total']} GB"),
            self.create_card("QUERIES TODAY", str(pihole.get("queries_today", "n/a"))),
            self.create_card("BLOCKED TODAY", str(pihole.get("blocked_today", "n/a"))),
            self.create_card("BLOCKED %", f"{pihole.get('percent_blocked', 'n/a')} %"),
            self.create_card("STATUS", str(pihole.get("status", "n/a"))),
        ]

    def format_fail2ban_text(self, fail2ban):
        if not fail2ban.get("enabled"):
            return "disabled"

        return (
            f"Total: {fail2ban.get('total_bans', 'n/a')}\n"
            f"Current: {fail2ban.get('currently_banned', 'n/a')}\n"
            f"Jails: {fail2ban.get('jail_count', 'n/a')}\n"
            f"IP: {fail2ban.get('last_listed_ip', 'n/a')}"
        )

    def render_offline_device(self, device):
        self.title_label.set_markup(
            f"<span size='26000' weight='bold'>{device['name']}</span>\n"
            f"<span size='13000'>{device['hostname']}</span>"
        )

        cards = [
            self.create_card(
                "STATUS",
                "OFFLINE",
                "offline-card"
            ),
            self.create_card(
                "ERROR",
                device.get("error", "Unknown error"),
                "offline-card"
            ),
        ]

        self.attach_cards(cards)

    def attach_cards(self, cards):
        positions = [
            (0, 0), (1, 0),
            (0, 1), (1, 1),
            (0, 2), (1, 2),
        ]

        for card, (column, row) in zip(cards, positions):
            self.cards_grid.attach(card, column, row, 1, 1)

    def previous_device(self, button=None):
        if self.current_index > 0:
            self.current_index -= 1
            self.render_device()

    def next_device(self, button=None):
        if self.current_index < len(self.devices) - 1:
            self.current_index += 1
            self.render_device()

    def update_navigation_buttons(self):
        self.prev_button.set_sensitive(self.current_index > 0)
        self.next_button.set_sensitive(self.current_index < len(self.devices) - 1)

    def update_refresh_label(self):
        if self.last_refresh_time:
            refresh_time = self.last_refresh_time.strftime("%H:%M:%S")
        else:
            refresh_time = "n/a"

        self.refresh_label.set_markup(
            f"<span size='10000'>Refresh: {REFRESH_INTERVAL_SECONDS}s | Last: {refresh_time}</span>"
        )

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

        .offline-card {
            background-color: #552222;
            border-radius: 14px;
            border: 2px solid #aa3333;
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
