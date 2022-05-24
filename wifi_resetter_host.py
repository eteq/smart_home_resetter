import sys
import time
import subprocess
from urllib.request import urlopen
from pathlib import Path
from typing import Optional
from multiprocessing import Process

import typer

import serial



def main(serialport: Path = typer.Argument(...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=True,
        resolve_path=True),
        hasspath: Path = typer.Argument(Path.home() / 'home_assistant',
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True),
        baudrate: int = typer.Option(115200),
        process_wait_time: float = typer.Option(1),
        verbose: bool = False
    ):
    procs = {}  # Popen objects for child processes

    if verbose:
        typer.echo(f"Using serial port {serialport} at baud rate {baudrate}")
    with serial.Serial(str(serialport), baudrate, timeout=1) as ser:
        lastline = b''
        while True:
            line = ser.readline()
            if line:
                if line.endswith(b'\n'):
                    line = (lastline + line).strip()
                    if line == b'status':
                        reply_status(ser, verbose, procs)
                    elif line == b'on':
                        hass_on(hasspath, verbose, procs, process_wait_time)
                    elif line == b'off':
                        hass_off(hasspath, verbose, procs, process_wait_time)
                    lastline = b''
                else:
                    typer.secho('Line cut off, reassembling next cycle', fg=typer.colors.YELLOW, bold=True)
                    lastline = line


def reply_status(ser, verbose, procs):
    if check_internet(verbose):
        retval = 1
    else:
        retval = 0
    if verbose:
        typer.echo(f'Got status request, returning {retval}')
    ser.write(str(retval).encode('ascii') + b'\r\n')


def hass_on(hasspath, verbose, procs, process_wait_time):
    typer.secho("Starting home assistant", fg=typer.colors.GREEN)
    if verbose:
        typer.echo(f'Got on with home assistant path {hasspath}')
    while 'on' in procs and procs['on'].poll() is None:
        typer.echo("on proc still running. Waiting for completion", fg=typer.colors.YELLOW, bold=True)
        time.sleep(process_wait_time)
    while 'off' in procs and procs['off'].poll() is None:
        typer.echo("off proc still running. Waiting for completion", fg=typer.colors.YELLOW, bold=True)
        time.sleep(process_wait_time)
    procs['on'] = subprocess.Popen('docker compose up -d', shell=True, cwd=hasspath)


def hass_off(hasspath, verbose, procs, process_wait_time):
    typer.secho("Restart requested. Stopping home assistant", fg=typer.colors.RED)
    if verbose:
        typer.echo(f'Got off with home assistant path {hasspath}')
    check_procs(procs, process_wait_time)
    procs['off'] = subprocess.Popen('docker compose down', shell=True, cwd=hasspath)\


def check_procs(procs, process_wait_time):
    while 'on' in procs and procs['on'].poll() is None:
        typer.echo(f'on proc still running. Waiting {process_wait_time} sec for'
                    ' completion', fg=typer.colors.YELLOW, bold=True)
        time.sleep(process_wait_time)
    while 'off' in procs and procs['off'].poll() is None:
        typer.echo(f'off proc still running. Waiting {process_wait_time} sec for'
                    ' completion', fg=typer.colors.YELLOW, bold=True)
        time.sleep(process_wait_time)

def check_internet(verbose, timeout):
    if verbose:
        typer.echo(f'Checking for internet')
    p = Process(target=_mp_do_internet_check)
    p.join(timeout)
    if p.is_alive():
        p.kill()
        if verbose:
            typer.secho(f'No response in timeout {timeout}', fg=typer.colors.RED)
        return False
    else:
        exc = p.exitcode
        if verbose and exc != 0:
            typer.secho(f'Succeeded before timeout {timeout}, but with exit code {exc}', fg=typer.colors.RED)
        return exc == 0


def _mp_do_internet_check():
    try:
        res = urlopen('http://www.example.com')
    except:
        sys.exit(1)
    if res.status == 200:
        sys.exit(0)
    else:
        sys.exit(-1)


if __name__ == "__main__":
    typer.run(main)