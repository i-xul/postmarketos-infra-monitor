#!/usr/bin/env python3

import subprocess
import json
from pathlib import Path


SSH_KEY = Path.home() / ".ssh" / "infra_monitor"

DEVICES = [
    {
        "name": "Ubuntu Server",
        "host": "192.168.1.11",
        "user": "hmasi"
    },
    {
        "name": "Raspberry Pi 4",
        "host": "192.168.1.111",
        "user": "hmasi"
    }
]


def run_ssh_command(host, command, user="hmasi", timeout=8):
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

    temp_raw = lines[1].strip()

    cpu_temp = float(
        temp_raw
        .replace("temp=", "")
        .replace("'C", "")
        .strip()
    )

    load_values = lines[2].strip().split()
    cpu_load = load_values[0]

    ram_used, ram_total = lines[3].strip().split()

    uptime = lines[4].replace("up ", "").strip()

    return {
        "name": device["name"],
        "hostname": hostname,
        "cpu_temp": cpu_temp,
        "cpu_load": cpu_load,
        "ram_used": round(int(ram_used) / 1024, 1),
        "ram_total": round(int(ram_total) / 1024, 1),
        "uptime": uptime,
        "fail2ban": {
            "total_bans": "n/a",
            "last_banned_ip": "n/a"
        }
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
