# HD6301 firmware sources

The assembly modules implement Typestar BASIC, its tokenized program storage, decimal arithmetic adapters, keyboard/LCD console, serial communication, audio and paper graphics.

| Prefix / files | Purpose |
|---|---|
| `basic*`, `console*`, `editor*`, `input*` | Interpreter entry points and console |
| `token*`, `program-store*`, `statement*` | Token records and statement dispatch |
| `decimal*`, `native-decimal*`, `math*`, `logic*` | Arithmetic, Canon math interfaces and logical expressions |
| `array*`, `string*` | Arrays and strings |
| `lcd*`, `keymap*`, `keyboard*` | Display and keyboard |
| `paper*`, `print*`, `graphics*` | Text, glyphs, drawing and motor control |
| `serial*`, `native-serial*`, `buzzer*` | Communications and sound |

Construction stages are in [tools/firmware](../tools/firmware/README.md). `firmware.json` describes the initial assembly stage; later stages carry the version forward to the current release. It is not the current release manifest. Standalone hardware probes are archived outside the public sources.
