#!/usr/bin/env python3
"""
Leak-rate and solenoid valve check for balloon and chuck circuits.

Tests at ~100 PSI and ~0 PSI for each circuit:
  - Pressurization SV (SV3 balloon / SV4 chuck)
  - Relief SV (SV5 balloon / SV6 chuck)

Run from this project folder:
  python tools/leak_test_valves.py

Data port COM9 (REPL is COM6). Close Run_Screen_1b.py before running.
"""

from __future__ import annotations

import argparse
import struct
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

# Allow "python tools/leak_test_valves.py" from project root.
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
ValveRole = Literal["press", "relief", "idle"]


@dataclass
class Telemetry:
    balloon_psi: float
    chuck_psi: float
    input_psi: float


@dataclass
class Sample:
    t_s: float
    pressure_psi: float
    input_psi: float


@dataclass
class LeakResult:
    circuit: str
    test_name: str
    valve_role: str
    target_psi: float
    p_start: float
    p_end: float
    duration_s: float
    rate_psi_per_min: float
    passed: bool
    note: str


def pack_cmd(
    *,
    circuit: Circuit = "balloon",
    valve: ValveRole = "idle",
    duty_pct: float = 100.0,
) -> bytes:
    """Build 100-byte command; only one circuit SV bank enabled at a time."""
    bal_sv = 0
    bal_press = 0.0
    bal_relief = 0.0
    chk_sv = 0
    chk_press = 0.0
    chk_relief = 0.0

    if circuit == "balloon" and valve != "idle":
        bal_sv = 1
        if valve == "press":
            bal_press = duty_pct
        else:
            bal_relief = duty_pct
    elif circuit == "chuck" and valve != "idle":
        chk_sv = 1
        if valve == "press":
            chk_press = duty_pct
        else:
            chk_relief = duty_pct

    return struct.pack(
        COMMAND_FMT,
        0,
        0.0,
        0,
        0.0,
        0,
        0,
        bal_sv,
        bal_press,
        bal_relief,
        chk_sv,
        chk_press,
        chk_relief,
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


def wait_for_packet(ser: serial.Serial, timeout_s: float = 3.0) -> Telemetry | None:
    idle = pack_cmd()
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        tele = read_once(ser, reply_cmd=idle)
        if tele:
            return tele
        time.sleep(0.05)
    return None


def all_valves_off(ser: serial.Serial) -> bytes:
    cmd = pack_cmd()
    ser.write(cmd)
    return cmd


def log_sample(
    circuit: Circuit,
    phase: str,
    sample: Sample,
    extra: str = "",
) -> None:
    suffix = f"  {extra}" if extra else ""
    print(
        f"[{sample.t_s:6.1f}s] {circuit:7} {phase:14}  "
        f"P={sample.pressure_psi:7.2f} psi  P_in={sample.input_psi:6.1f}{suffix}",
        flush=True,
    )


def poll_with_valves(
    ser: serial.Serial,
    *,
    circuit: Circuit,
    valve: ValveRole,
    duration_s: float,
    duty_pct: float,
    phase: str,
    interval_s: float,
) -> tuple[list[Sample], Telemetry]:
    cmd = pack_cmd(circuit=circuit, valve=valve, duty_pct=duty_pct)
    ser.write(cmd)
    t0 = time.monotonic()
    samples: list[Sample] = []
    last = Telemetry(0.0, 0.0, 0.0)
    while True:
        elapsed = time.monotonic() - t0
        if elapsed >= duration_s:
            break
        tele = read_once(ser, reply_cmd=cmd)
        if tele:
            last = tele
            p = circuit_pressure(tele, circuit)
            sample = Sample(elapsed, p, tele.input_psi)
            samples.append(sample)
            log_sample(
                circuit,
                phase,
                sample,
                f"{valve}={duty_pct:.0f}%",
            )
        else:
            time.sleep(0.05)
        time.sleep(max(0.0, interval_s - 0.05))
    return samples, last


def fill_to_target(
    ser: serial.Serial,
    *,
    circuit: Circuit,
    target_psi: float,
    max_s: float,
    interval_s: float,
) -> Telemetry:
    cmd = pack_cmd(circuit=circuit, valve="press", duty_pct=100.0)
    ser.write(cmd)
    t0 = time.monotonic()
    last = Telemetry(0.0, 0.0, 0.0)
    print(f"\n  Filling {circuit} toward {target_psi:.0f} psi (press SV 100%) ...", flush=True)
    while time.monotonic() - t0 < max_s:
        elapsed = time.monotonic() - t0
        tele = read_once(ser, reply_cmd=cmd)
        if tele:
            last = tele
            p = circuit_pressure(tele, circuit)
            log_sample(circuit, "FILL", Sample(elapsed, p, tele.input_psi))
            if p >= target_psi:
                print(f"  Target {target_psi:.0f} psi reached at t={elapsed:.1f}s\n", flush=True)
                break
        time.sleep(interval_s)
    else:
        print(f"  WARN: fill timeout ({max_s:.0f}s) before {target_psi:.0f} psi\n", flush=True)
    return last


def vent_to_zero(
    ser: serial.Serial,
    *,
    circuit: Circuit,
    zero_tol_psi: float,
    max_s: float,
    interval_s: float,
) -> Telemetry:
    cmd = pack_cmd(circuit=circuit, valve="relief", duty_pct=100.0)
    ser.write(cmd)
    t0 = time.monotonic()
    last = Telemetry(0.0, 0.0, 0.0)
    print(f"\n  Venting {circuit} toward 0 psi (relief SV 100%) ...", flush=True)
    while time.monotonic() - t0 < max_s:
        elapsed = time.monotonic() - t0
        tele = read_once(ser, reply_cmd=cmd)
        if tele:
            last = tele
            p = circuit_pressure(tele, circuit)
            log_sample(circuit, "VENT", Sample(elapsed, p, tele.input_psi))
            if p <= zero_tol_psi:
                print(f"  At or below {zero_tol_psi:.1f} psi at t={elapsed:.1f}s\n", flush=True)
                break
        time.sleep(interval_s)
    else:
        print(f"  WARN: vent timeout ({max_s:.0f}s), P={circuit_pressure(last, circuit):.2f} psi\n", flush=True)
    return last


def hold_leak_rate(
    ser: serial.Serial,
    *,
    circuit: Circuit,
    hold_s: float,
    interval_s: float,
    phase: str,
) -> tuple[float, float, float]:
    idle = all_valves_off(ser)
    t0 = time.monotonic()
    p_start = 0.0
    p_end = 0.0
    started = False
    while True:
        elapsed = time.monotonic() - t0
        if elapsed >= hold_s:
            break
        tele = read_once(ser, reply_cmd=idle)
        if tele:
            p = circuit_pressure(tele, circuit)
            if not started:
                p_start = p
                started = True
            p_end = p
            log_sample(circuit, phase, Sample(elapsed, p, tele.input_psi))
        time.sleep(interval_s)
    duration = max(hold_s, 1e-6)
    return p_start, p_end, duration


def rate_psi_per_min(delta: float, duration_s: float) -> float:
    if duration_s <= 0:
        return 0.0
    return (delta / duration_s) * 60.0


def judge_hold_at_pressure(max_drop_psi: float, rate: float, limit_drop: float, limit_rate: float) -> tuple[bool, str]:
    if max_drop_psi > limit_drop or rate > limit_rate:
        return False, f"drop {max_drop_psi:.2f} psi ({rate:.2f} psi/min) exceeds limit"
    return True, f"hold loss {max_drop_psi:.2f} psi ({rate:.2f} psi/min)"


def judge_creep_at_zero(rise: float, rate: float, limit_rise: float, limit_rate: float) -> tuple[bool, str]:
    if rise > limit_rise or rate > limit_rate:
        return False, f"creep +{rise:.2f} psi ({rate:.2f} psi/min) exceeds limit"
    return True, f"creep +{rise:.2f} psi ({rate:.2f} psi/min)"


def judge_valve_action(
    delta: float,
    min_delta: float,
    role: ValveRole,
) -> tuple[bool, str]:
    if role == "press":
        if delta < min_delta:
            return False, f"press SV weak: only +{delta:.2f} psi"
        return True, f"press SV raised +{delta:.2f} psi"
    if role == "relief":
        if delta < min_delta:
            return False, f"relief SV weak: only -{delta:.2f} psi"
        return True, f"relief SV dropped -{delta:.2f} psi"
    return True, "idle"


def run_circuit_tests(
    ser: serial.Serial,
    circuit: Circuit,
    *,
    target_high_psi: float,
    zero_tol_psi: float,
    hold_high_s: float,
    hold_zero_s: float,
    valve_action_s: float,
    fill_max_s: float,
    vent_max_s: float,
    log_interval_s: float,
    limit_hold_drop_psi: float,
    limit_hold_rate: float,
    limit_zero_rise_psi: float,
    limit_zero_rate: float,
    min_press_action_psi: float,
    min_relief_action_psi: float,
) -> list[LeakResult]:
    results: list[LeakResult] = []
    label = circuit.upper()

    print(f"\n{'=' * 72}", flush=True)
    print(f"  CIRCUIT: {label}", flush=True)
    print(f"{'=' * 72}", flush=True)

    print(f"\n--- {label}: HOLD LEAK @ {target_high_psi:.0f} PSI (both SVs OFF) ---", flush=True)
    vent_to_zero(
        ser,
        circuit=circuit,
        zero_tol_psi=zero_tol_psi,
        max_s=vent_max_s,
        interval_s=log_interval_s,
    )
    all_valves_off(ser)
    time.sleep(1.0)
    fill_to_target(
        ser,
        circuit=circuit,
        target_psi=target_high_psi,
        max_s=fill_max_s,
        interval_s=log_interval_s,
    )
    all_valves_off(ser)
    time.sleep(0.5)
    p_start, p_end, dur = hold_leak_rate(
        ser,
        circuit=circuit,
        hold_s=hold_high_s,
        interval_s=log_interval_s,
        phase="HOLD-100",
    )
    drop = p_start - p_end
    rate = rate_psi_per_min(drop, dur)
    ok, note = judge_hold_at_pressure(drop, rate, limit_hold_drop_psi, limit_hold_rate)
    results.append(
        LeakResult(
            circuit=circuit,
            test_name=f"hold @ {target_high_psi:.0f} psi",
            valve_role="both off",
            target_psi=target_high_psi,
            p_start=p_start,
            p_end=p_end,
            duration_s=dur,
            rate_psi_per_min=rate,
            passed=ok,
            note=note,
        )
    )

    print(f"\n--- {label}: CREEP @ 0 PSI (both SVs OFF after vent) ---", flush=True)
    vent_to_zero(
        ser,
        circuit=circuit,
        zero_tol_psi=zero_tol_psi,
        max_s=vent_max_s,
        interval_s=log_interval_s,
    )
    all_valves_off(ser)
    time.sleep(0.5)
    p_start, p_end, dur = hold_leak_rate(
        ser,
        circuit=circuit,
        hold_s=hold_zero_s,
        interval_s=log_interval_s,
        phase="HOLD-0",
    )
    rise = p_end - p_start
    rate = rate_psi_per_min(rise, dur)
    ok, note = judge_creep_at_zero(rise, rate, limit_zero_rise_psi, limit_zero_rate)
    results.append(
        LeakResult(
            circuit=circuit,
            test_name="creep @ 0 psi",
            valve_role="both off",
            target_psi=0.0,
            p_start=p_start,
            p_end=p_end,
            duration_s=dur,
            rate_psi_per_min=rate,
            passed=ok,
            note=note,
        )
    )

    print(f"\n--- {label}: PRESSURIZATION SV (SV3/SV4) @ 0 -> fill ---", flush=True)
    vent_to_zero(
        ser,
        circuit=circuit,
        zero_tol_psi=zero_tol_psi,
        max_s=vent_max_s,
        interval_s=log_interval_s,
    )
    all_valves_off(ser)
    tele = wait_for_packet(ser) or Telemetry(0.0, 0.0, 0.0)
    p_before = circuit_pressure(tele, circuit)
    _, tele_after = poll_with_valves(
        ser,
        circuit=circuit,
        valve="press",
        duration_s=valve_action_s,
        duty_pct=100.0,
        phase="PRESS-SV",
        interval_s=log_interval_s,
    )
    all_valves_off(ser)
    p_after = circuit_pressure(tele_after, circuit)
    delta = p_after - p_before
    ok, note = judge_valve_action(delta, min_press_action_psi, "press")
    results.append(
        LeakResult(
            circuit=circuit,
            test_name="press SV action",
            valve_role="press",
            target_psi=target_high_psi,
            p_start=p_before,
            p_end=p_after,
            duration_s=valve_action_s,
            rate_psi_per_min=rate_psi_per_min(delta, valve_action_s),
            passed=ok,
            note=note,
        )
    )

    print(f"\n--- {label}: RELIEF SV (SV5/SV6) @ high -> vent ---", flush=True)
    fill_to_target(
        ser,
        circuit=circuit,
        target_psi=target_high_psi,
        max_s=fill_max_s,
        interval_s=log_interval_s,
    )
    all_valves_off(ser)
    tele = wait_for_packet(ser) or Telemetry(0.0, 0.0, 0.0)
    p_before = circuit_pressure(tele, circuit)
    _, tele_after = poll_with_valves(
        ser,
        circuit=circuit,
        valve="relief",
        duration_s=valve_action_s,
        duty_pct=100.0,
        phase="RELIEF-SV",
        interval_s=log_interval_s,
    )
    all_valves_off(ser)
    p_after = circuit_pressure(tele_after, circuit)
    delta = p_before - p_after
    ok, note = judge_valve_action(delta, min_relief_action_psi, "relief")
    results.append(
        LeakResult(
            circuit=circuit,
            test_name="relief SV action",
            valve_role="relief",
            target_psi=0.0,
            p_start=p_before,
            p_end=p_after,
            duration_s=valve_action_s,
            rate_psi_per_min=rate_psi_per_min(delta, valve_action_s),
            passed=ok,
            note=note,
        )
    )

    all_valves_off(ser)
    return results


def print_summary(results: list[LeakResult]) -> int:
    print(f"\n{'=' * 72}", flush=True)
    print("  LEAK / VALVE TEST SUMMARY", flush=True)
    print(f"{'=' * 72}", flush=True)
    print(
        f"{'Circuit':<8} {'Test':<22} {'Valve':<10} "
        f"{'P start':>8} {'P end':>8} {'Rate':>10} {'Result':<6} Note",
        flush=True,
    )
    print("-" * 72, flush=True)

    failures = 0
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        if not r.passed:
            failures += 1
        print(
            f"{r.circuit:<8} {r.test_name:<22} {r.valve_role:<10} "
            f"{r.p_start:8.2f} {r.p_end:8.2f} {r.rate_psi_per_min:9.2f}/m "
            f"{status:<6} {r.note}",
            flush=True,
        )

    print("-" * 72, flush=True)
    if failures:
        print(f"  OVERALL: FAIL ({failures} of {len(results)} checks failed)", flush=True)
    else:
        print(f"  OVERALL: PASS ({len(results)} checks)", flush=True)
    print(flush=True)
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--port",
        default=PICO_DATA_PORT,
        help=f"Data/telemetry port (REPL is on COM6; default {PICO_DATA_PORT})",
    )
    parser.add_argument("--target-psi", type=float, default=100.0, help="High-pressure hold target (psi)")
    parser.add_argument("--zero-tol-psi", type=float, default=1.0, help="Consider vented when below this (psi)")
    parser.add_argument("--hold-high-s", type=float, default=60.0, help="Hold duration at high pressure (s)")
    parser.add_argument("--hold-zero-s", type=float, default=45.0, help="Hold duration at zero pressure (s)")
    parser.add_argument("--valve-action-s", type=float, default=15.0, help="Duration for press/relief SV checks (s)")
    parser.add_argument("--fill-max-s", type=float, default=180.0, help="Max fill time per step (s)")
    parser.add_argument("--vent-max-s", type=float, default=60.0, help="Max vent time per step (s)")
    parser.add_argument("--log-interval-s", type=float, default=0.5, help="Telemetry print interval (s)")
    parser.add_argument("--limit-hold-drop-psi", type=float, default=2.0, help="Max drop during high hold")
    parser.add_argument("--limit-hold-rate", type=float, default=2.0, help="Max drop rate at high hold (psi/min)")
    parser.add_argument("--limit-zero-rise-psi", type=float, default=1.0, help="Max rise during zero hold")
    parser.add_argument("--limit-zero-rate", type=float, default=1.0, help="Max creep rate at zero (psi/min)")
    parser.add_argument("--min-press-action-psi", type=float, default=5.0, help="Min rise during press SV test")
    parser.add_argument("--min-relief-action-psi", type=float, default=5.0, help="Min drop during relief SV test")
    parser.add_argument(
        "--circuits",
        default="balloon,chuck",
        help="Comma-separated: balloon, chuck, or both",
    )
    args = parser.parse_args()

    circuits: list[Circuit] = []
    for part in args.circuits.split(","):
        name = part.strip().lower()
        if name in ("balloon", "chuck"):
            circuits.append(name)  # type: ignore[arg-type]
    if not circuits:
        print("No valid circuits in --circuits", file=sys.stderr)
        return 2

    print(f"Connecting {args.port} @ 115200 ...", flush=True)
    ser = serial.Serial(args.port, 115200, timeout=0.05)
    time.sleep(0.3)

    all_results: list[LeakResult] = []
    try:
        tele = wait_for_packet(ser)
        if not tele:
            print(
                f"No telemetry on {args.port} — is Pico running? Close Run_Screen_1b.py first.",
                file=sys.stderr,
            )
            return 1
        print(
            f"\nLink OK  P_in={tele.input_psi:.1f}  "
            f"P_balloon={tele.balloon_psi:.2f}  P_chuck={tele.chuck_psi:.2f} psi\n",
            flush=True,
        )
        if tele.input_psi < args.target_psi + 10.0:
            print(
                f"  WARN: supply P_in={tele.input_psi:.1f} psi may be low for "
                f"{args.target_psi:.0f} psi target\n",
                flush=True,
            )

        common = dict(
            target_high_psi=args.target_psi,
            zero_tol_psi=args.zero_tol_psi,
            hold_high_s=args.hold_high_s,
            hold_zero_s=args.hold_zero_s,
            valve_action_s=args.valve_action_s,
            fill_max_s=args.fill_max_s,
            vent_max_s=args.vent_max_s,
            log_interval_s=args.log_interval_s,
            limit_hold_drop_psi=args.limit_hold_drop_psi,
            limit_hold_rate=args.limit_hold_rate,
            limit_zero_rise_psi=args.limit_zero_rise_psi,
            limit_zero_rate=args.limit_zero_rate,
            min_press_action_psi=args.min_press_action_psi,
            min_relief_action_psi=args.min_relief_action_psi,
        )

        for circuit in circuits:
            all_results.extend(run_circuit_tests(ser, circuit, **common))

        return print_summary(all_results)
    finally:
        all_valves_off(ser)
        time.sleep(0.2)
        ser.close()
        print("All valves OFF. Port closed.", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
