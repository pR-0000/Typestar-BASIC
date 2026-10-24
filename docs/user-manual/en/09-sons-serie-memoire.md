# 9 - Making sound and exchanging information

A short signal can announce a correct answer. A serial connection can preserve a program on your computer or send information to another device. These functions add possibilities while keeping the same BASIC lines.

<a id="beep"></a>
<a id="sound"></a>
## BEEP and SOUND: a signal, effect or pause

![Printy introduces sound: beeps, pauses and effects give programs a rhythm.](../images/illustration-sons.png)

`BEEP` plays a beep lasting approximately 100 milliseconds. Supply a duration from **0 to 2000 milliseconds**: `BEEP 200` plays for two tenths of a second.

`SOUND rate,duration` modulates the buzzer for the requested time. Rate is an integer from **50 to 31250 hertz**, duration an integer from **0 to 2000 milliseconds**. The special value zero gives a silent pause:

```basic
10 SOUND 300,100
20 SOUND 0,50
30 SOUND 450,150
```

The program plays a little two-part signal. `SOUND 0,1000` waits approximately one second silently, a simple way to leave a message readable. Chain pauses or use a loop for waits longer than two seconds.

During BEEP and SOUND, execution waits until the signal or pause ends. These are **blocking** statements, for a maximum of two seconds per command. The signal runs continuously; the keyboard is sampled again afterwards. To interrupt the program, hold **BREAK** until the sound ends. Durations are nominal, suitable for pacing messages and effects.

`SOUND rate,duration[,duty[,texture]]` offers two additional controls. **Duty** ranges from 1 to 99%, default 50%: it changes level and timbre by setting the proportion of time with the buzzer enabled. **Texture** is 0 for a square gate waveform or 1 for a pseudo-random 31-bit pattern. The latter uses 1000–31250 bits/s, ignores duty and temporarily borrows 672 free bytes.

```basic
10 SOUND 5500,180,50
20 SOUND 8000,250,50,1
30 FOR D=10 TO 90 STEP 10:SOUND 5890,30,D:NEXT D
```

The first sound uses a high gate rate, the second a noise pattern, and the third a level envelope. The firmware drives the buzzer gate; machine resonance and mixing produce different perceived pitches. Rate describes the electrical command. Musical tuning also depends on the transducer. Duration follows a whole number of periods, or 31-bit patterns for noise: resolution reaches 20 ms at the slowest rates and 31 ms for noise. Very short requests play at least one cycle; zero duration returns immediately. Extreme duty ratios are rounded to achievable timings. **Piano** offers nine modes to explore these effects.

## Keeping your program on a computer

![The cable connects your program to the computer: Studio keeps a copy for later.](../images/illustration-liaison.png)

Serial backup copies **the program** into a computer file; variables are recreated during execution. Use the Typestar cable, which adapts USB to **5 V TTL signals** and the machine's DE-9 pinout.

Launch **Typestar BASIC Studio.pyw**. At the bottom, select the cable's serial port; its name and description help identify the FTDI adapter. Click **Refresh** after connecting it. Port names differ on Windows, Linux and macOS; choose the one listed for your adapter.

Studio and the machine must have matching settings. BASIC starts at **31250 baud, 7E1**: select **Baud 31250**, **parity E** and **Stop 1** in Studio. The software already selects seven data bits. If the Canon's settings have changed, match both ends before transfer.

![Studio transfer buttons: Send towards LOAD, Receive from SAVE.](images/studio-transferts.png)

![Printy keeps a copy: SAVE and Studio preserve the program on the computer.](../images/printy-memoire.png)

<a id="save"></a>
<a id="load"></a>
### SAVE sends, LOAD receives

**Saving from the Canon to the computer:**

1. Click **Receive ← SAVE** in Studio, or choose **Program > Receive from Canon (SAVE)…**.
2. Name the backup file, for example `my-game.bas`, and select its folder.
3. When Studio asks, type `SAVE` and press Return on the Canon.
4. Wait for Studio's reception confirmation. The file is written after complete reception; you can then open it in the editor.

**Loading from the computer to the Canon:**

1. Open your `.bas` file in Studio, or write a small program. The editor's current lines are what will be sent.
2. Click **Send → LOAD**, or choose **Program > Send to Canon (LOAD)…**. Confirm replacement of the machine's program.
3. When Studio asks, type `LOAD` and press Return on the Canon. LOADING shows reception in progress.
4. Wait for Studio's transfer confirmation. Type `LIST` to review the program or `RUN` to start it.

**LOAD replaces the Canon's current program.** Back it up with Receive ← SAVE before loading another game. Remember the directions: **LOAD brings a program into the Canon; SAVE sends it out to the computer**.

LOAD and SAVE are **console commands**. Interrupted loading may leave a partial program: resolve the cause, repeat the complete transfer, then check with LIST and RUN. Your computer backup preserves the earlier program.

Files remain UTF-8 on the computer. Studio converts recognised LCD accents and restores them when receiving. Its transfer buttons bring the required steps together.

**To troubleshoot a transfer**, check the chosen port, cable, requested LOAD or SAVE command and both ends' settings. Wait for Studio's instruction before confirming on the Canon. After interruption, use Cancel if Studio still has an active transfer, return to the Canon console with BREAK, then repeat the whole operation.

<a id="baud"></a>
<a id="sercfg"></a>
## BAUD and SERCFG: setting up the conversation

```basic
BAUD 31250
SERCFG 7E1
```

BAUD selects **1200, 2400, 7812, 15625 or 31250**. The number 7812 denotes the corresponding hardware setting; choose the same option on the computer.

SERCFG selects the character format, **without quotation marks**. The first digit is always 7: seven data bits. N means no parity, E even parity, O odd parity. The final digit selects one or two stop bits. The six formats are **7N1, 7N2, 7E1, 7E2, 7O1 and 7O2**.

Parity adds a small check to each character, handled by hardware. **Choose the same format at both ends**, such as 7E1.

BAUD and SERCFG apply to program transfers, computer graphics printing and serial sessions. Close a session with SERCLOSE before changing them. `BAUD 1200` allows communication with older equipment accepting that rate.

<a id="seropen"></a>
<a id="serout"></a>
<a id="serin"></a>
<a id="serclose"></a>
## SEROPEN, SEROUT, SERIN and SERCLOSE: talking from a program

`SEROPEN rate` opens a session at that rate using SERCFG's format. `SEROUT code` sends **0 to 127**. `SERIN(0)` reads without waiting: it returns a received code from 0 to 127, or **-1** while waiting for a character. SERCLOSE finishes transmission and closes the session.

For SERIN, **zero is valid serial data**; **-1 means no data available**. Its argument is always zero.

This echo program waits for a character from the computer, then sends the same code back:

```basic
10 SERCFG 7E1
20 SEROPEN 31250
30 A=SERIN(0)
40 IF A=-1 THEN 30
50 SEROUT A
60 SERCLOSE
70 END
```

To try it, open the computer end with matching settings and send a raw character. The program exchanges codes directly using its own conversation.

Organise exchanges as **one character, one reply**. The program chooses when to listen and how to answer. This pace suits its small receive reserve, especially during calculation or printing. The cable supplies the required control signals.

Write **SERCLOSE before END**, and close the session before LOAD, SAVE, another SEROPEN or a settings change. Errors and BREAK also close communication. These functions provide a foundation for a remote keyboard or simple terminal; your program supplies the protocol.

**Try the remote keyboard.** The `examples/remote-keyboard/` directory supplies the BASIC program and Python peer, with a bilingual guide. Load the program with Studio, start the script on the PC, then type RUN on the Canon. Monitor mode displays key codes; `--type` converts them into keystrokes in your chosen window. Letters, recognised accents, Enter, Backspace and navigation travel over the serial connection at 31250/7E1.

## Printing an image from the computer

At the BASIC console, **CODE + P** opens serial graphics-printer mode. This shortcut is for direct use. Studio prepares and sends a monochrome image using the appropriate protocol.

This mode can borrow program memory for its buffer: **the first validated print block may perform NEW**. CODE+P initially opens a waiting state. Save your program before sending and close any SEROPEN session.

<a id="peek"></a>
<a id="poke"></a>
## PEEK and POKE: looking beneath the cover

These tools suit readers beginning to explore memory and peripherals. `PEEK(address)` reads a byte. `POKE address,value` writes a byte. Address is an integer from **0 to 65535**; the written value is **0 to 255**.

```basic
PRINT PEEK(&H4000)
```

This reads the first byte of the CPU area occupied by external ROM. The result depends on firmware. PEEK uses processor addresses, whereas a ROM file stores image bytes.

POKE writes directly to memory or hardware registers. Use it at addresses whose purpose you understand, with a backup saved before exploring: an incorrect write can alter the program or trigger an action. Dedicated BASIC commands simplify ordinary drawing, sound and movement.

**What about reading a cartridge?** PEEK observes memory currently visible to the processor. Accessing a cartridge also requires selecting its bank, then restoring normal memory: some windows share addresses with the BASIC program itself. A future cartridge reader will need to perform this short operation in an always-accessible routine, then pass the bytes to a BASIC program and its serial peer on the PC.
