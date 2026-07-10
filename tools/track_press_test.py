#!/usr/bin/env python3
"""
Pressurization tracking test — balloon and chuck (clamp) circuits.

For each target pressure (0–100 psi):
  1. Start near 0 psi
  2. Enable closed-loop tracking to the target
  3. Measure rise time, overshoot, and 10 s stability (±0.1 psi)

Run from the RPI project folder:
  python tools/track_press_test.py
  python tools/track_press_test.py --targets 25,50,75,100
  python tools/track_press_test.py --no-log-csv

Per-sample CSV (includes P_in) is written to logs/ by default.

Close Run_Screen_1b.py first (COM9 data port).
"""

from __future__ import annotations

import argparse
import csv
import random
import struct
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from serial_ports import PICO_DATA_PORT  # noqa: E402

try:
    import serial
except ImportError:
    print("pip install pyserial", file=sys.stderr)
    raise SystemExit(1)

TELEMETRY_FMT = "fffbb13sbfbb10s"
TELEMETRY_SIZE = struct.calcsize(TELEMETRY_FMT)
COMMAND_FMT = "ififiiiffiffiiiifiiiifiii"

Circuit = Literal["balloon", "chuck"]
STABILITY_BAND_PSI = 0.1
STABILITY_HOLD_S = 10.0


@dataclass
class Telemetry:
    balloon_psi: float
    chuck_psi: float
    input_psi: float


@dataclass
class TrackSample:
    t_s: float
    circuit_psi: float
    balloon_psi: float
    chuck_psi: float
    input_psi: float


@dataclass
class TrackStepResult:
    circuit: str
    target_psi: float
    p_start: float
    rise_time_s: float | None
    overshoot_psi: float
    peak_psi: float
    valley_psi: float
    stable_10s: bool
    max_deviation_psi: float
    passed: bool
    input_psi_start: float = 0.0
    input_psi_min: float = 0.0
    input_psi_max: float = 0.0
    input_psi_range: float = 0.0
    samples: list[TrackSample] = field(default_factory=list)
    notes: str = ""


def pack_cmd(
    *,
    track_balloon: bool = False,
    target_balloon: float = 0.0,
    track_chuck: bool = False,
    target_chuck: float = 0.0,
    enable_balloon_sv: bool = False,
    balloon_press_pct: float = 0.0,
    balloon_relief_pct: float = 0.0,
    enable_chuck_sv: bool = False,
    chuck_press_pct: float = 0.0,
    chuck_relief_pct: float = 0.0,
) -> bytes:
    return struct.pack(
        COMMAND_FMT,
        int(track_balloon),
        float(target_balloon),
        int(track_chuck),
        float(target_chuck),
        0,
        0,
        int(enable_balloon_sv),
        float(balloon_press_pct),
        float(balloon_relief_pct),
        int(enable_chuck_sv),
        float(chuck_press_pct),
        float(chuck_relief_pct),
        0,
        0,
        0,
        0,
        0.0,
        0,
        0,
        0,
        0,
        0.0,
        0,
        0,
        0,
    )


def circuit_pressure(tele: Telemetry, circuit: Circuit) -> float:
    return tele.balloon_psi if circuit == "balloon" else tele.chuck_psi


def fmt_press_line(
    elapsed: float,
    tele: Telemetry,
    circuit: Circuit,
    *,
    suffix: str = "",
) -> str:
    p = circuit_pressure(tele, circuit)
    extra = f"  {suffix}" if suffix else ""
    return (
        f"    [{elapsed:6.2f}s] P={p:6.2f} psi  "
        f"P_in={tele.input_psi:6.2f} psi{extra}"
    )


def write_samples_csv(path: Path, results: list[TrackStepResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "circuit",
                "target_psi",
                "t_s",
                "circuit_psi",
                "balloon_psi",
                "chuck_psi",
                "input_psi",
            ]
        )
        for r in results:
            for s in r.samples:
                writer.writerow(
                    [
                        r.circuit,
                        f"{r.target_psi:.1f}",
                        f"{s.t_s:.3f}",
                        f"{s.circuit_psi:.3f}",
                        f"{s.balloon_psi:.3f}",
                        f"{s.chuck_psi:.3f}",
                        f"{s.input_psi:.3f}",
                    ]
                )


def read_once(ser: serial.Serial, reply_cmd: bytes | None = None) -> Telemetry | None:
    waiting = ser.in_waiting
    if waiting > TELEMETRY_SIZE:
        ser.read(waiting)
        return None
    if waiting != TELEMETRY_SIZE:
        return None
    u = struct.unpack(TELEMETRY_FMT, ser.read(TELEMETRY_SIZE))
    if reply_cmd is not None:
        ser.write(reply_cmd)
    return Telemetry(float(u[0]), float(u[1]), float(u[2]))


def wait_for_packet(ser: serial.Serial, cmd: bytes, timeout_s: float = 3.0) -> Telemetry | None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        tele = read_once(ser, reply_cmd=cmd)
        if tele:
            return tele
        time.sleep(0.02)
    return None


def all_off_cmd() -> bytes:
    return pack_cmd()


def vent_both_cmd() -> bytes:
    return pack_cmd(
        enable_balloon_sv=True,
        balloon_relief_pct=100.0,
        enable_chuck_sv=True,
        chuck_relief_pct=100.0,
    )


def vent_cmd(circuit: Circuit) -> bytes:
    if circuit == "balloon":
        return pack_cmd(enable_balloon_sv=True, balloon_relief_pct=100.0)
    return pack_cmd(enable_chuck_sv=True, chuck_relief_pct=100.0)


def track_cmd(circuit: Circuit, target_psi: float) -> bytes:
    if circuit == "balloon":
        return pack_cmd(track_balloon=True, target_balloon=target_psi)
    return pack_cmd(track_chuck=True, target_chuck=target_psi)


def vent_both_to_zero(
    ser: serial.Serial,
    *,
    zero_tol_psi: float,
    max_s: float,
    interval_s: float,
) -> tuple[float, float]:
    cmd = vent_both_cmd()
    off = all_off_cmd()
    t0 = time.monotonic()
    last_bal = 999.0
    last_chk = 999.0
    last_in = 999.0
    print(f"  Venting balloon + chuck to <= {zero_tol_psi:.1f} psi ...", flush=True)
    while time.monotonic() - t0 < max_s:
        tele = read_once(ser, reply_cmd=cmd)
        if tele:
            last_bal = tele.balloon_psi
            last_chk = tele.chuck_psi
            last_in = tele.input_psi
            print(
                f"    P_balloon={last_bal:6.2f}  P_chuck={last_chk:6.2f}  "
                f"P_in={last_in:6.2f} psi",
                flush=True,
            )
            if last_bal <= zero_tol_psi and last_chk <= zero_tol_psi:
                break
        time.sleep(interval_s)
    ser.write(off)
    time.sleep(0.3)
    return last_bal, last_chk


def vent_to_zero(
    ser: serial.Serial,
    circuit: Circuit,
    *,
    zero_tol_psi: float,
    max_s: float,
    interval_s: float,
) -> float:
    off = all_off_cmd()
    cmd = vent_cmd(circuit)
    ser.write(off)
    time.sleep(0.35)
    t0 = time.monotonic()
    last_p = 999.0
    last_in = 999.0
    stall_t0 = t0
    stall_p = 999.0
    print(f"  Venting {circuit} to <= {zero_tol_psi:.1f} psi ...", flush=True)
    while time.monotonic() - t0 < max_s:
        tele = read_once(ser, reply_cmd=cmd)
        if tele:
            last_p = circuit_pressure(tele, circuit)
            last_in = tele.input_psi
            print(
                f"    P={last_p:6.2f} psi  P_in={last_in:6.2f} psi",
                flush=True,
            )
            if last_p <= zero_tol_psi:
                break
            if abs(last_p - stall_p) < 0.05:
                if time.monotonic() - stall_t0 >= 8.0:
                    print(
                        f"    WARN: vent stalled near {last_p:.2f} psi for 8s",
                        flush=True,
                    )
                    stall_t0 = time.monotonic()
            else:
                stall_p = last_p
                stall_t0 = time.monotonic()
        time.sleep(interval_s)
    ser.write(off)
    time.sleep(0.3)
    return last_p


def parse_targets_arg(text: str) -> list[float]:
    out: list[float] = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        v = float(part)
        if not 0.0 <= v <= 100.0:
            raise ValueError(f"Target {v} outside 0–100 psi")
        out.append(v)
    return out


def prompt_targets() -> list[float]:
    print("\nEnter target pressures (0–100 psi). Blank line when done.\n", flush=True)
    targets: list[float] = []
    while True:
        try:
            line = input(f"  Target #{len(targets) + 1} psi: ").strip()
        except EOFError:
            break
        if not line:
            break
        v = float(line)
        if not 0.0 <= v <= 100.0:
            print("    Must be between 0 and 100.", flush=True)
            continue
        targets.append(v)
    return targets


def random_targets(count: int, seed: int | None) -> list[float]:
    rng = random.Random(seed)
    return [round(rng.uniform(5.0, 100.0), 1) for _ in range(count)]


def in_band(p: float, target: float, band: float) -> bool:
    return abs(p - target) <= band


def run_tracking_step(
    ser: serial.Serial,
    circuit: Circuit,
    target_psi: float,
    *,
    approach_max_s: float,
    interval_s: float,
    stability_s: float,
    stability_band: float,
    overshoot_limit: float,
    vent_other_circuit: bool = False,
) -> TrackStepResult:
    if vent_other_circuit:
        other: Circuit = "chuck" if circuit == "balloon" else "balloon"
        vent_to_zero(ser, other, zero_tol_psi=1.0, max_s=60.0, interval_s=interval_s)

    vent_to_zero(ser, circuit, zero_tol_psi=1.0, max_s=90.0, interval_s=interval_s)

    tele = wait_for_packet(ser, all_off_cmd()) or Telemetry(0.0, 0.0, 0.0)
    p_start = circuit_pressure(tele, circuit)
    input_start = tele.input_psi
    input_min = input_start
    input_max = input_start
    samples: list[TrackSample] = []

    cmd = track_cmd(circuit, target_psi)
    ser.write(cmd)

    print(
        f"\n  Tracking {circuit} -> {target_psi:.1f} psi  "
        f"(started at {p_start:.2f} psi, P_in={input_start:.2f} psi)",
        flush=True,
    )

    t0 = time.monotonic()
    rise_time: float | None = None
    peak = p_start
    valley = p_start
    stable_ok = False
    max_dev = 0.0
    stability_samples: list[tuple[float, float]] = []
    t_stable_start: float | None = None
    stability_breaks = 0
    max_stable_breaks = 8
    going_up = target_psi >= p_start
    last_log_t = -1.0

    settle_budget_s = stability_s + 20.0 + max_stable_breaks * 5.0
    deadline = t0 + approach_max_s + settle_budget_s

    while time.monotonic() < deadline:
        elapsed = time.monotonic() - t0
        tele = read_once(ser, reply_cmd=cmd)
        if not tele:
            time.sleep(0.02)
            continue

        p = circuit_pressure(tele, circuit)
        peak = max(peak, p)
        valley = min(valley, p)
        input_min = min(input_min, tele.input_psi)
        input_max = max(input_max, tele.input_psi)
        samples.append(
            TrackSample(elapsed, p, tele.balloon_psi, tele.chuck_psi, tele.input_psi)
        )
        in_target_band = in_band(p, target_psi, stability_band)

        if in_target_band:
            if rise_time is None:
                rise_time = elapsed
                print(
                    fmt_press_line(elapsed, tele, circuit, suffix="reached band"),
                    flush=True,
                )
            if t_stable_start is None:
                t_stable_start = time.monotonic()
                if stability_breaks > 0:
                    print(
                        fmt_press_line(
                            elapsed,
                            tele,
                            circuit,
                            suffix=f"back in band — restart {stability_s:.0f}s hold",
                        ),
                        flush=True,
                    )

            dev = abs(p - target_psi)
            max_dev = max(max_dev, dev)
            stability_samples.append((time.monotonic() - t_stable_start, p))

            if time.monotonic() - t_stable_start >= stability_s:
                stable_ok = True
                print(
                    f"    Stable for {stability_s:.0f}s within ±{stability_band:.1f} psi",
                    flush=True,
                )
                break
        else:
            if t_stable_start is not None:
                print(
                    fmt_press_line(
                        elapsed,
                        tele,
                        circuit,
                        suffix=(
                            f"STABILITY BREAK (>{stability_band:.1f} psi from target)"
                        ),
                    ),
                    flush=True,
                )
                stable_ok = False
                t_stable_start = None
                stability_samples.clear()
                stability_breaks += 1
                if stability_breaks >= max_stable_breaks:
                    print(
                        f"    Aborted: {max_stable_breaks} stability breaks",
                        flush=True,
                    )
                    break

            if rise_time is None:
                if elapsed - last_log_t >= 0.8:
                    print(fmt_press_line(elapsed, tele, circuit), flush=True)
                    last_log_t = elapsed
            elif stability_breaks > 0 and elapsed - last_log_t >= 2.0:
                print(
                    fmt_press_line(elapsed, tele, circuit, suffix="settling"),
                    flush=True,
                )
                last_log_t = elapsed

        time.sleep(interval_s)

    if going_up:
        overshoot = max(0.0, peak - target_psi)
    else:
        overshoot = max(0.0, target_psi - valley)

    notes: list[str] = []
    if rise_time is None:
        notes.append("never reached target band")
    if not stable_ok:
        notes.append(f"not stable {stability_s:.0f}s within ±{stability_band:.1f} psi")
    if overshoot > stability_band:
        notes.append(f"overshoot {overshoot:.2f} psi")
    input_range = input_max - input_min
    if input_range > 2.0:
        notes.append(f"P_in range {input_range:.2f} psi ({input_min:.1f}–{input_max:.1f})")

    passed = (
        rise_time is not None
        and stable_ok
        and overshoot <= overshoot_limit
    )

    return TrackStepResult(
        circuit=circuit,
        target_psi=target_psi,
        p_start=p_start,
        rise_time_s=rise_time,
        overshoot_psi=overshoot,
        peak_psi=peak,
        valley_psi=valley,
        stable_10s=stable_ok,
        max_deviation_psi=max_dev,
        passed=passed,
        input_psi_start=input_start,
        input_psi_min=input_min,
        input_psi_max=input_max,
        input_psi_range=input_range,
        samples=samples,
        notes="; ".join(notes) if notes else "ok",
    )


def print_summary(results: list[TrackStepResult]) -> int:
    print(f"\n{'=' * 80}", flush=True)
    print("  TRACKING TEST SUMMARY", flush=True)
    print(f"{'=' * 80}", flush=True)
    print(
        f"{'Circuit':<8} {'Target':>7} {'Start':>7} {'Rise s':>7} "
        f"{'Overshoot':>9} {'P_in rng':>8} {'10s OK':>7} {'Result':<6} Notes",
        flush=True,
    )
    print("-" * 80, flush=True)

    fails = 0
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        if not r.passed:
            fails += 1
        rise = f"{r.rise_time_s:.2f}" if r.rise_time_s is not None else "  —"
        stable = "yes" if r.stable_10s else "no"
        pin_rng = f"{r.input_psi_range:.1f}"
        print(
            f"{r.circuit:<8} {r.target_psi:7.1f} {r.p_start:7.2f} {rise:>7} "
            f"{r.overshoot_psi:9.2f} {pin_rng:>8} {stable:>7} {status:<6} {r.notes}",
            flush=True,
        )

    print("-" * 80, flush=True)
    if fails:
        print(f"  OVERALL: FAIL ({fails} of {len(results)} steps)", flush=True)
    else:
        print(f"  OVERALL: PASS ({len(results)} steps)", flush=True)
    print(flush=True)
    return 1 if fails else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--port", default=PICO_DATA_PORT)
    parser.add_argument(
        "--targets",
        default="",
        help="Comma-separated targets 0–100 psi (e.g. 25,50,75,100)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for each target pressure",
    )
    parser.add_argument(
        "--random",
        type=int,
        default=0,
        metavar="N",
        help="Use N random targets instead of --targets",
    )
    parser.add_argument("--seed", type=int, default=None, help="RNG seed for --random")
    parser.add_argument(
        "--circuits",
        default="balloon,chuck",
        help="balloon, chuck, or both",
    )
    parser.add_argument("--approach-max-s", type=float, default=180.0, help="Max time to reach target")
    parser.add_argument("--stability-s", type=float, default=STABILITY_HOLD_S)
    parser.add_argument("--stability-band", type=float, default=STABILITY_BAND_PSI)
    parser.add_argument("--log-interval-s", type=float, default=0.25)
    parser.add_argument("--overshoot-limit", type=float, default=1.0, help="Fail if overshoot exceeds this")
    parser.add_argument(
        "--log-csv",
        default="",
        metavar="PATH",
        help="Per-sample CSV path (default: logs/track_press_<timestamp>.csv)",
    )
    parser.add_argument("--no-log-csv", action="store_true", help="Do not write per-sample CSV")
    args = parser.parse_args()

    circuits: list[Circuit] = []
    for part in args.circuits.split(","):
        name = part.strip().lower()
        if name in ("balloon", "chuck"):
            circuits.append(name)  # type: ignore[arg-type]
    if not circuits:
        print("No valid circuits.", file=sys.stderr)
        return 2

    if args.interactive:
        targets = prompt_targets()
    elif args.random > 0:
        targets = random_targets(args.random, args.seed)
    elif args.targets.strip():
        try:
            targets = parse_targets_arg(args.targets)
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 2
    else:
        targets = [25.0, 50.0, 75.0, 100.0]

    if not targets:
        print("No targets to test.", file=sys.stderr)
        return 2

    print(f"Connecting {args.port} ...", flush=True)
    print(f"Targets: {targets}", flush=True)
    print(f"Circuits: {circuits}", flush=True)

    ser = serial.Serial(args.port, 115200, timeout=0.05)
    time.sleep(0.3)
    results: list[TrackStepResult] = []

    try:
        tele = wait_for_packet(ser, all_off_cmd())
        if not tele:
            print(f"No telemetry on {args.port} — close Run_Screen_1b.py first.", file=sys.stderr)
            return 1
        print(
            f"\nLink OK  P_in={tele.input_psi:.1f}  "
            f"P_balloon={tele.balloon_psi:.2f}  P_chuck={tele.chuck_psi:.2f}\n",
            flush=True,
        )

        for circuit in circuits:
            print(f"\n{'=' * 80}", flush=True)
            print(f"  CIRCUIT: {circuit.upper()}", flush=True)
            print(f"{'=' * 80}", flush=True)
            if circuit == "chuck":
                vent_both_to_zero(
                    ser,
                    zero_tol_psi=1.0,
                    max_s=90.0,
                    interval_s=args.log_interval_s,
                )
            for target in targets:
                print(f"\n--- {circuit}: target {target:.1f} psi ---", flush=True)
                step = run_tracking_step(
                    ser,
                    circuit,
                    target,
                    approach_max_s=args.approach_max_s,
                    interval_s=args.log_interval_s,
                    stability_s=args.stability_s,
                    stability_band=args.stability_band,
                    overshoot_limit=args.overshoot_limit,
                    vent_other_circuit=(circuit == "chuck"),
                )
                results.append(step)
                ser.write(all_off_cmd())
                time.sleep(0.5)

        exit_code = print_summary(results)
        if not args.no_log_csv:
            if args.log_csv:
                csv_path = Path(args.log_csv)
            else:
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_path = _TOOLS_DIR.parent / "logs" / f"track_press_{stamp}.csv"
            write_samples_csv(csv_path, results)
            print(f"Sample log: {csv_path}", flush=True)
        return exit_code
    finally:
        ser.write(all_off_cmd())
        time.sleep(0.2)
        ser.close()
        print("Tracking OFF. Port closed.", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
