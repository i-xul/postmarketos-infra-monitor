#!/usr/bin/env python3

import subprocess
import json
from pathlib import Path

def run_ssh_command(host, command, user="hmasi", timeout=8):
    ssh_target = f"{user}@{host}"

    result = subprocess.run(
        [
    "ssh",
    "-i", str(Path.home() / ".ssh" / "infra_monitor"),
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


def get_raspberry_pi_telemetry(host, user="hmasi"):
    command = """
hostname
vcgencmd measure_temp 2>/dev/null || echo "temp=0.0'C"
cut -d ' ' -f1-3 /proc/loadavg
free -m | awk '/Mem:/ {print $3, $2}'
uptime -p
"""

    output = run_ssh_command(host, command, user=user)
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
        "name": "Ubuntu Server",
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


if __name__ == "__main__":
    device = get_raspberry_pi_telemetry("192.168.1.11")
    print(json.dumps(device, indent=2))
