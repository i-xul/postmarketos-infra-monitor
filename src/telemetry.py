#!/usr/bin/env python3

import json
import re
import subprocess
from pathlib import Path


SSH_KEY = Path.home() / ".ssh" / "infra_monitor"

DEVICES = [
    {
        "name": "Ubuntu Server",
        "host": "192.168.1.11",
        "user": "hmasi",
        "fail2ban": False,
        "pihole": False,
    },
    {
        "name": "Raspberry Pi 4",
        "host": "192.168.1.111",
        "user": "hmasi",
        "fail2ban": True,
        "pihole": False,
    },
    {
        "name": "Pi-hole",
        "host": "192.168.1.222",
        "user": "hmasi",
        "fail2ban": False,
        "pihole": True,
    },
]


def run_ssh_command(host, command, user="hmasi", timeout=10):
    ssh_target = f"{user}@{host}"

    result = subprocess.run(
        [
            "ssh",
            "-i", str(SSH_KEY),
            "-o", "BatchMode=yes",
            "-o", f"ConnectTimeout={timeout}",
            ssh_target,
            command,
        ],
        capture_output=True,
        text=True,
        timeout=timeout + 2,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    return result.stdout.strip()


def parse_temperature(temp_raw):
    return float(
        temp_raw
        .replace("temp=", "")
        .replace("'C", "")
        .strip()
    )


def parse_jail_list(status_output):
    for line in status_output.splitlines():
        if "Jail list:" in line:
            jail_part = line.split("Jail list:", 1)[1]
            return [
                jail.strip()
                for jail in jail_part.split(",")
                if jail.strip()
            ]

    return []


def parse_fail2ban_jail_status(jail_output):
    total_banned = 0
    currently_banned = 0
    banned_ips = []

    for line in jail_output.splitlines():
        line = line.strip()

        if "Currently banned:" in line:
            value = line.split("Currently banned:", 1)[1].strip()
            if value.isdigit():
                currently_banned = int(value)

        elif "Total banned:" in line:
            value = line.split("Total banned:", 1)[1].strip()
            if value.isdigit():
                total_banned = int(value)

        elif "Banned IP list:" in line:
            ip_part = line.split("Banned IP list:", 1)[1].strip()
            banned_ips = re.findall(r"(?:\d{1,3}\.){3}\d{1,3}", ip_part)

    return {
        "currently_banned": currently_banned,
        "total_banned": total_banned,
        "banned_ips": banned_ips,
    }


def get_fail2ban_telemetry(device):
    if not device.get("fail2ban"):
        return {
            "enabled": False,
            "jail_count": "n/a",
            "total_bans": "n/a",
            "currently_banned": "n/a",
            "last_listed_ip": "n/a",
        }

    status_output = run_ssh_command(
        host=device["host"],
        user=device["user"],
        command="sudo fail2ban-client status",
    )

    jails = parse_jail_list(status_output)

    total_bans = 0
    currently_banned = 0
    all_banned_ips = []

    for jail in jails:
        jail_output = run_ssh_command(
            host=device["host"],
            user=device["user"],
            command=f"sudo fail2ban-client status {jail}",
        )

        jail_status = parse_fail2ban_jail_status(jail_output)

        total_bans += jail_status["total_banned"]
        currently_banned += jail_status["currently_banned"]
        all_banned_ips.extend(jail_status["banned_ips"])

    last_listed_ip = all_banned_ips[-1] if all_banned_ips else "n/a"

    return {
        "enabled": True,
        "jail_count": len(jails),
        "total_bans": total_bans,
        "currently_banned": currently_banned,
        "last_listed_ip": last_listed_ip,
    }


def parse_pihole_stats(stats_output):
    stats = {}

    for line in stats_output.splitlines():
        parts = line.strip().split(maxsplit=1)

        if len(parts) == 2:
            key, value = parts
            stats[key] = value

    queries_today = int(stats.get("dns_queries_today", 0))
    blocked_today = int(stats.get("ads_blocked_today", 0))
    percent_blocked = float(stats.get("ads_percentage_today", 0.0))
    status = stats.get("status", "unknown")

    return {
        "enabled": True,
        "queries_today": queries_today,
        "blocked_today": blocked_today,
        "percent_blocked": round(percent_blocked, 1),
        "status": status,
    }


def get_pihole_telemetry(device):
    if not device.get("pihole"):
        return {
            "enabled": False,
            "queries_today": "n/a",
            "blocked_today": "n/a",
            "percent_blocked": "n/a",
            "status": "n/a",
        }

    stats_output = run_ssh_command(
        host=device["host"],
        user=device["user"],
        command='echo -e ">stats\\n>quit" | nc 127.0.0.1 4711',
    )

    return parse_pihole_stats(stats_output)


def get_linux_telemetry(device):
    command = """
hostname

if command -v vcgencmd >/dev/null 2>&1; then
    vcgencmd measure_temp
else
    if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
        awk '{print "temp=" $1/1000 "\\047C"}' /sys/class/thermal/thermal_zone0/temp
    else
        echo "temp=0.0'C"
    fi
fi

cut -d ' ' -f1-3 /proc/loadavg
free -m | awk '/Mem:/ {print $3, $2}'
uptime -p
"""

    output = run_ssh_command(
        host=device["host"],
        user=device["user"],
        command=command,
    )

    lines = output.splitlines()

    hostname = lines[0].strip()
    cpu_temp = parse_temperature(lines[1].strip())

    load_values = lines[2].strip().split()
    cpu_load = load_values[0]

    ram_used, ram_total = lines[3].strip().split()
    uptime = lines[4].replace("up ", "").strip()

    fail2ban = get_fail2ban_telemetry(device)
    pihole = get_pihole_telemetry(device)

    return {
        "name": device["name"],
        "hostname": hostname,
        "cpu_temp": cpu_temp,
        "cpu_load": cpu_load,
        "ram_used": round(int(ram_used) / 1024, 1),
        "ram_total": round(int(ram_total) / 1024, 1),
        "uptime": uptime,
        "fail2ban": fail2ban,
        "pihole": pihole,
    }


def collect_all_devices():
    results = []

    for device in DEVICES:
        try:
            telemetry = get_linux_telemetry(device)
            results.append(telemetry)

        except Exception as error:
            results.append(
                {
                    "name": device["name"],
                    "hostname": device["host"],
                    "offline": True,
                    "error": str(error),
                }
            )

    return results


if __name__ == "__main__":
    print(
        json.dumps(
            collect_all_devices(),
            indent=2
        )
    )
