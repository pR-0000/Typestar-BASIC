"""ROM selection and process transport for Studio; no firmware PC hooks.

Known BASIC images opt into basic_adapter. All other images use the experimental
hardware machine. Execution stays in a child process; never opens a serial port.
"""
import json
import queue
import sys
import threading
import time
from core import VERSION


def emit(value):
    print(json.dumps(value, ensure_ascii=True), flush=True)


def backend(realtime_sound=False, mask_path=None, firmware_path=None, cold_start=False,
            mode='auto', layout='auto', cartridge_path=None):
    from cartridge import load_cartridge
    cartridge=load_cartridge(cartridge_path)
    # Legacy no-argument defaults are used only by offline BASIC regressions.
    if mask_path is None or firmware_path is None:
        if cartridge:raise ValueError('Font cartridges currently require generic ROM mode')
        if mode == 'generic':raise ValueError('Generic mode requires both ROM paths')
        from basic_adapter import basic_backend
        return basic_backend(realtime_sound, mask_path, firmware_path, cold_start, layout=layout)
    from rom_images import load_roms
    image, mask, symbols, info = load_roms(mask_path, firmware_path, mode, layout)
    if info['basic_available']:
        if cartridge:raise ValueError('Font cartridges currently require generic ROM mode')
        from basic_adapter import basic_backend
        return basic_backend(realtime_sound, mask_path, firmware_path, cold_start,
                             layout=info['layout'])
    from machine import GenericMachine
    class SelectedMachine(GenericMachine):
        def __init__(self, source=''):
            super().__init__(image, mask, cartridge=cartridge)
            if source:self.request_run(source)
    return SelectedMachine


def main():
    commands = queue.Queue()
    def reader():
        for line in sys.stdin:
            try:
                commands.put(json.loads(line))
            except ValueError:
                commands.put({'op': 'invalid'})
        commands.put({'op': 'quit'})
    threading.Thread(target=reader, daemon=True).start()
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--mask-rom',required=True)
    parser.add_argument('--firmware-rom',required=True)
    parser.add_argument('--mode', choices=('auto','generic','basic'), default='auto')
    parser.add_argument('--layout', choices=('auto','socket','cpu'), default='auto')
    parser.add_argument('--cartridge-rom')
    args=parser.parse_args()
    from rom_images import load_roms
    _,_,_,rom_info=load_roms(args.mask_rom,args.firmware_rom,args.mode,args.layout)
    CPU = backend(realtime_sound=True,mask_path=args.mask_rom,firmware_path=args.firmware_rom,cold_start=True,mode=args.mode,layout=args.layout,cartridge_path=args.cartridge_rom)
    cpu = CPU()
    paused = False
    sound_scale = 1.0
    instant_paper = False
    pause_started = 0
    last = 0
    emit({'type': 'ready', 'version': VERSION, 'realtime_sound': True, 'roms':rom_info,'cartridge':cpu.cartridge.metadata() if getattr(cpu,'cartridge',None) else None})
    while True:
        try:
            while not commands.empty():
                command = commands.get_nowait()
                op = command.get('op')
                if op == 'quit': return
                if op == 'run':
                    cpu.request_run(command.get('source',''))
                    paused=False
                elif op == 'reset':
                    cpu = CPU()
                    cpu.sound_scale=sound_scale
                    cpu.instant_paper=instant_paper
                    emit(dict(type='paper_reset'))
                    paused = False
                elif op == 'sound_scale':
                    sound_scale=max(1.,min(3.,float(command['value'])))
                    cpu.sound_scale=sound_scale
                elif op == 'instant_paper':
                    instant_paper=bool(command['value'])
                    cpu.instant_paper=instant_paper
                elif op == 'debug':
                    from debugger import inspect_cpu
                    emit(inspect_cpu(cpu,cpu.symbols,command.get('address',cpu.pc)))
                elif op == 'pause':
                    next_paused=bool(command['value'])
                    if next_paused and not paused:pause_started=time.monotonic()
                    if paused and not next_paused and cpu.sound_until:
                        cpu.sound_until+=time.monotonic()-pause_started
                    paused=next_paused
                elif op == 'break':
                    cpu.request_break(); paused = False
                elif op in ('key_press','held_key'):
                    value=command['value']
                    if not isinstance(value,int) or not 0<=value<128:raise ValueError('Code clavier invalide')
                    if op=='key_press':cpu.key_press(value)
                    else:cpu.release_logical(value) if cpu.basic_available else setattr(cpu,'held_key',value)
                elif op == 'code_toggle':
                    if cpu.basic_available:cpu.toggle_code()
                    else:
                        cpu.host_matrix([0x3b]);cpu.host_matrix([])
                elif op == 'host_matrix':
                    cpu.host_matrix(command.get('keys',[]),command.get('shift',False),command.get('cancel',False))
                elif op == 'matrix':
                    if cpu.basic_available:raise ValueError('Matrix input requires generic mode')
                    cpu.set_matrix(command['keys'],command.get('shift',False))
                elif op == 'keys':
                    if not cpu.basic_available:raise ValueError('ASCII injection requires a BASIC profile')
                    values = command['values']
                    if len(cpu.input)+len(values) > 256 or any(not isinstance(v, int) or not 0 <= v < 128 for v in values):
                        raise ValueError('Touches ASCII attendues, 256 maximum.')
                    cpu.input.extend(values)
            if not paused:
                for _ in range(3000):
                    cpu.step()
                    if cpu.audio_events:
                        for event in cpu.audio_events:emit(dict(type='audio',**event))
                        cpu.audio_events.clear()
                    if cpu.sound_until:break
                if cpu.sound_until or getattr(cpu,'waiting',None):time.sleep(.002)
            else:
                time.sleep(.01)
            if time.monotonic()-last > .08:
                if cpu.paper_events:
                    emit(dict(type='paper',columns=cpu.paper_events))
                    cpu.paper_events.clear()
                emit(cpu.snapshot(paused))
                last = time.monotonic()
                # The regression backend records verbose traces. Bound them for
                # interactive sessions (jobs remains a cumulative counter).
                for name in ('columns', 'map_tiles', 'paper_heat_y', 'lcd_characters', 'frames', 'sounds'):
                    values = getattr(cpu, name, [])
                    if len(values) > 1024: del values[:-512]
                cpu.lcd_commands.clear()
        except Exception as exc:
            paused = True
            emit({'type': 'error', 'message': f'{type(exc).__name__}: {exc} (PC {cpu.pc:04X})'})


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        emit({'type': 'error', 'message': 'Initialisation impossible : '+str(exc)})
        sys.exit(1)
