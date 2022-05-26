import sys
import time
import json
import subprocess
from urllib import request
from urllib.error import HTTPError
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
        internet_wait_time: float = typer.Option(0.4),
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
                    if line == b'inet_status':
                        reply_status(ser, verbose, procs, internet_wait_time)
                    if line == b'hass_status':
                        reply_hass_status(ser, verbose)
                    elif line == b'on':
                        hass_on(hasspath, verbose, procs, process_wait_time)
                    elif line == b'off':
                        hass_off(hasspath, verbose, procs, process_wait_time)
                    lastline = b''
                else:
                    typer.secho('Line cut off, reassembling next cycle', fg=typer.colors.YELLOW, bold=True)
                    lastline = line


def reply_status(ser, verbose, procs, internet_wait_time):
    if check_internet(verbose, internet_wait_time):
        retval = 1
    else:
        retval = 0
    if verbose:
        typer.echo(f'Got status request, returning {retval}')
    ser.write(str(retval).encode('ascii') + b'\n')


auth_token = []
def reply_hass_status(ser, verbose):
    retval = None

    # get the authorization token from the file if it hasn't yet been loaded
    if not auth_token:
        if Path('hass_auth_token').is_file():
            with open('hass_auth_token') as f:
                auth_token.append(f.read().strip())
        else:
            auth_token.append(None)

    headers = {"content-type": "application/json"}
    if auth_token and auth_token[0] is not None:
        headers['Authorization'] = "Bearer " + auth_token[0]

    req = request.Request('http://localhost:8123/api/config', headers=headers)
    try:
        u = request.urlopen(req)
    except HTTPError as e:
        if e.status == 401:
            typer.secho('Unauthorized! Need to fix token. Proceeding hoping its up.', fg=typer.colors.RED, bold=True)
            retval = 1
        u = None
    except Exception as e:
        if verbose:
            typer.secho('url request did not complete to hass API server - maybe still turning on?')
        retval = 0
        u = None

    if u is not None:
        j = json.loads(u.read())
        retval = j['state'] == 'RUNNING'

    if verbose:
        typer.echo(f'Got hass status request, returning {retval}')
    ser.write(str(retval).encode('ascii') + b'\n')


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
    p.start()
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
        res = request.urlopen('http://www.example.com')
    except:
        sys.exit(1)
    if res.status == 200:
        sys.exit(0)
    else:
        sys.exit(-1)


if __name__ == "__main__":
    typer.run(main)