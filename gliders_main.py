#!/usr/bin/env python
# coding: utf-8

import argparse
import datetime
import os
import subprocess
import sys


def build_log_path(log_dir, prefix="gliders_main"):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.log"
    return os.path.join(log_dir, filename)


def run_script(script_name, cmd, log_handle):
    start_time = datetime.datetime.now().strftime("%Y-%b-%d %H:%M:%S")
    header = f"\n=== Running {script_name} at {start_time} ===\n"
    print(header, end="")
    log_handle.write(header)
    log_handle.flush()

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if proc.stdout is not None:
        for line in proc.stdout:
            print(line, end="")
            log_handle.write(line)

    proc.wait()

    footer = f"=== Exit code {proc.returncode} ===\n"
    print(footer, end="")
    log_handle.write(footer)
    log_handle.flush()

    return proc.returncode


def main():
    parser = argparse.ArgumentParser(
        description="Wrapper for NANOOS glider processing scripts."
    )
    parser.add_argument(
        "-t",
        "--transect",
        required=True,
        help="Transect name (e.g., washelf, lapush, osu_trinidad1).",
    )
    parser.add_argument(
        "-d",
        "--deployment",
        help="Deployment name for plotting (optional).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run gliders_check_transect_deployments.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run check then plots (same as running both).",
    )
    parser.add_argument(
        "--plots",
        action="store_true",
        help="Run gliders_make_plots.",
    )
    parser.add_argument(
        "--log-file",
        help="Path to log file. If omitted, a timestamped log is created in ./logs.",
    )
    parser.add_argument(
        "--log-dir",
        default="logs",
        help="Directory for timestamped logs when --log-file is not set.",
    )

    args = parser.parse_args()

    run_check = args.all or args.check or (not args.check and not args.plots and not args.all)
    run_plots = args.all or args.plots or (not args.check and not args.plots and not args.all)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = args.log_dir

    if args.log_file:
        log_path = args.log_file
        log_dir = os.path.dirname(os.path.abspath(log_path))
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
    else:
        os.makedirs(log_dir, exist_ok=True)
        log_path = build_log_path(log_dir)

    print(f"Log file: {log_path}")

    with open(log_path, "w", encoding="utf-8") as log_handle:
        log_handle.write(f"Log started: {datetime.datetime.now().isoformat()}\n")

        if run_check:
            check_script = os.path.join(script_dir, "gliders_check_transect_deployments.py")
            check_cmd = [sys.executable, check_script, "-t", args.transect]
            exit_code = run_script("gliders_check_transect_deployments", check_cmd, log_handle)
            if exit_code != 0:
                sys.exit(exit_code)

        if run_plots:
            plots_script = os.path.join(script_dir, "gliders_make_plots.py")
            plots_cmd = [sys.executable, plots_script, "-t", args.transect]
            if args.deployment:
                plots_cmd.extend(["-d", args.deployment])
            exit_code = run_script("gliders_make_plots", plots_cmd, log_handle)
            if exit_code != 0:
                sys.exit(exit_code)


if __name__ == "__main__":
    main()
