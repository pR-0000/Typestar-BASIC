"""First-run installer. Only modifies studio/.venv, never system Python."""
import os
from pathlib import Path
import subprocess
import sys

PROBE="import PySide6.QtWidgets,PySide6.QtMultimedia,serial,PIL.Image,capstone"

def command(args,log):
    result=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,
        **({'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}))
    if result.returncode:raise RuntimeError('Installation échouée (code %s). Voir studio-install.log.'%result.returncode)

def ensure_environment(here,progress):
    python=here/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    with (here/'studio-install.log').open('a',encoding='utf-8') as log:
        if not python.exists():
            progress('Création de l’environnement Python local…')
            command([sys.executable,'-m','venv',str(here/'.venv')],log)
        probe=subprocess.run([str(python),'-c',PROBE],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
            **({'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}))
        if probe.returncode:
            progress('Installation des dépendances… Une connexion Internet est nécessaire.')
            command([str(python),'-m','pip','install','--disable-pip-version-check','-r',str(here/'internal/requirements.txt')],log)
            command([str(python),'-c',PROBE],log)
    return python

def launch(here):
    # No startup window: normal checks and first-time installation are silent.
    try:
        python=ensure_environment(here,lambda message: None)
        if os.name=='nt':python=python.with_name('pythonw.exe')
        subprocess.Popen([str(python),str(here/'internal/app.py')],cwd=str(here),
            **({'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}))
    except Exception as exc:
        message=f"Unable to start Typestar BASIC Studio: {exc}\nSee {here/'studio-install.log'}"
        with (here/'studio-install.log').open('a',encoding='utf-8') as log:
            log.write(message+'\n')
        # Only failures need attention; Tk is not required for a normal launch.
        try:
            import tkinter as tk
            from tkinter import messagebox
            window=tk.Tk()
            window.withdraw()
            try:messagebox.showerror('Typestar BASIC Studio',message,parent=window)
            finally:window.destroy()
        except Exception:
            if sys.stderr is not None:print(message,file=sys.stderr)
