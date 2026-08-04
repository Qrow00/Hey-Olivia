import argparse
import csv
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run(args) -> str:
    try:
        return subprocess.run(
            args, capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        ).stdout.strip()
    except Exception:
        return ""


def read_gpu() -> dict:
    out = _run([
        "nvidia-smi",
        "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
        "--format=csv,noheader,nounits",
    ])
    parts = [p.strip() for p in out.split(",")]
    if len(parts) >= 5:
        return {
            "gpu_name": parts[0],
            "gpu_load": parts[1],
            "gpu_mem_used_mb": parts[2],
            "gpu_mem_total_mb": parts[3],
            "gpu_temp": parts[4],
        }
    return {}


def read_cpu_temp() -> str:
    out = _run([
        "powershell", "-NoProfile", "-Command",
        "(Get-CimInstance -ClassName Win32_PerfFormattedData_Counters_ThermalZoneInformation).Temperature",
    ])
    if out.isdigit():
        return f"{int(out) / 10:.1f}"
    return ""


def start_shutdown_watchdog(out_path: Path):
    ps = (
        "$log = r'{0}'\n"
        "try {{ Register-WmiEvent -Query \"SELECT * FROM Win32_ComputerShutdownEvent\" "
        "-SourceIdentifier diag -Action {{ Add-Content -Path $log -Value "
        "('SHUTDOWN_EVENT`t' + (Get-Date -Format o)) }} | Out-Null }} catch {{}}\n"
        "while ($true) {{ Start-Sleep -Seconds 2 }}"
    ).format(out_path)
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", ps],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Real-time thermal/power logger for shutdown diagnosis")
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    out_dir = Path(args.output or Path(__file__).resolve().parents[2] / "data" / "logs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"thermal_diag_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tsv"

    fields = [
        "ts", "ts_iso", "cpu_percent", "cpu_temp", "gpu_temp", "gpu_load",
        "gpu_mem_used_mb", "gpu_mem_total_mb", "ram_percent", "bat_percent",
        "ac_plugged", "marker",
    ]

    with out_path.open("w", newline="", buffering=1) as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()

        start_shutdown_watchdog(out_path)

        print(f"[THERMAL] logging to {out_path} every {args.interval}s — Ctrl+C to stop", flush=True)

        try:
            while True:
                row = {"ts": round(time.time(), 1), "ts_iso": iso_now(), "marker": ""}

                try:
                    row["cpu_percent"] = round(psutil.cpu_percent(interval=0.2), 1)
                except Exception:
                    pass
                row["cpu_temp"] = read_cpu_temp()
                row.update(read_gpu())

                try:
                    row["ram_percent"] = round(psutil.virtual_memory().percent, 1)
                except Exception:
                    pass

                try:
                    bat = psutil.sensors_battery()
                    if bat:
                        row["bat_percent"] = int(bat.percent)
                        row["ac_plugged"] = bat.power_plugged
                except Exception:
                    pass

                writer.writerow(row)
                time.sleep(args.interval)

        except KeyboardInterrupt:
            writer.writerow({"ts": round(time.time(), 1), "ts_iso": iso_now(), "marker": "MANUAL_STOP"})
            print("\n[THERMAL] stopped", flush=True)


if __name__ == "__main__":
    main()
