# MusicScore QuOM

A from-scratch audio synthesis engine in Python. It reads standard MIDI files (or manual note input), runs them through a physics-based oscillator + ADSR envelope pipeline, and writes 16-bit PCM WAV files. There's also a Tkinter GUI with a sheet music renderer if you want to see what you're hearing.

Built as a Master 2 Physics project to explore the intersection of signal processing, OOP design, and musical acoustics — all without relying on audio libraries like `pygame` or `pydub`. The synthesis math is written by hand: `math.sin()`, `struct.pack()`, and a lot of sample-by-sample loops.

## What it actually does

- Parses `.mid` files (via `mido`) and converts MIDI events into `Note` objects with frequency, start time, and duration
- Generates waveforms sample-by-sample at 44100 Hz using sine, square, or sawtooth oscillators
- Applies a linear ADSR envelope (attack ramp-up, release fade-out) to prevent clicks and simulate acoustic damping
- Mixes multiple simultaneous notes via additive synthesis (superposition — same principle as real sound waves)
- Runs an optional effects chain: hard-clipping distortion then feedback delay (echo), in that order
- Quantises the float mix buffer to 16-bit signed PCM and writes a valid WAV file header
- Displays Western music notation on a Tkinter Canvas — note heads, stems, beams, ledger lines, accidentals

## Getting started

You need Python 3.x and two packages:

```bash
pip install mido matplotlib
```

`mido` handles MIDI binary parsing. `matplotlib` is only used for the Piano Roll visualisation in the GUI — the core engine doesn't need it.

**Quick test** — generate a C major chord as a WAV file:

```bash
cd 1st_ver
python music_engine.py
```

This creates `test_mix.wav` (C4 + E4 + G4, arpeggiated over 2 seconds). If that works, the engine is good.

**Launch the GUI:**

```bash
python gui_enhance_test_khoa.py
```

Two tabs:
- **MIDI Converter** — browse for a `.mid` file, pick your oscillator and effects, hit Render
- **Acoustics Lab** — type a melody like `C4:0.5 E4:0.5 G4:1.0`, see the sheet music update, render to WAV

**Batch convert a MIDI file to all three waveforms:**

```bash
python play_midi.py
```

This reads `house_at_pooh_corner.mid` and outputs `_sine.wav`, `_square.wav`, and `_saw.wav` variants.

## Project layout

```
MusicScore_QuOM/
├── README.md
├── house_at_pooh_corner.mid         # sample MIDI for testing
│
├── 1st_ver/
│   ├── music_engine.py              # Note, Synthesizer, Score, AudioEffect classes
│   ├── play_midi.py                 # MIDI parser → Score builder
│   ├── sheet_music.py               # SheetMusicPanel (tk.Canvas subclass)
│   ├── gui_enhance_test_khoa.py     # main GUI application
│   └── examples/
│       ├── gui.py                   # older minimal GUI (kept for reference)
│       └── gui_staff.py             # early composer prototype
│
└── *.wav                            # generated output files (gitignored)
```

## How the synthesis works

The core loop in `Synthesizer.render_track()` does this:

1. **Allocate a float buffer** — length = (last note end + release tail + 0.5s) × 44100 samples. Everything stays as floats during mixing to avoid premature clipping.

2. **For each Note, generate samples** — at every sample index `i`:
   - Compute `t = i / 44100`
   - Sine: `sin(2π × freq × t)`
   - Square: `sign(sin(2π × freq × t))` — so +1 or -1
   - Sawtooth: `2 × ((t × freq) mod 1) - 1` — linear ramp

3. **Apply the ADSR envelope** — linear fade-in over the attack period, full amplitude in the middle, linear fade-out over the release period. This is what prevents the "click" you'd get from an instantaneous start.

4. **Add to the mix buffer** — `buffer[start + i] += sample × envelope × velocity × volume_adjustment`. The `+=` is the superposition: multiple notes just add together, exactly like real pressure waves.

5. **Run the effects chain** — distortion first (hard clip at `threshold = 1.0 - drive`, then renormalise), delay second (add `buffer[i - delay_samples] × decay` to the current sample).

6. **Quantise to PCM** — clamp each float to [-1.0, 1.0], multiply by 32767, pack as a little-endian signed 16-bit integer (`struct.pack('<h', value)`). Write the whole thing with Python's `wave` module.

The pitch calculation uses standard 12-tone equal temperament: `f = 440 × 2^((n - 57) / 12)` where `n` is the absolute semitone index (C0 = 0, A4 = 57). This is cached with `@lru_cache` so repeated notes don't recompute.

## The OOP structure (short version)

**`Note`** (dataclass) — four fields: `frequency`, `start_time`, `duration`, `velocity`. Factory method `from_name("C#4")` handles the string-to-Hz conversion. Static methods wrap the module-level parsing/frequency utilities.

**`Synthesizer`** — holds the oscillator type, ADSR parameters, and an ordered list of `AudioEffect` objects. The `render_track(notes)` method is where all the physics happens.

**`Score`** — container that owns a `list[Note]` and a `Synthesizer`. `save_to_wav()` triggers the render and writes the file. This is the object that gets passed around between the parser, the GUI, and the visualiser.

**`AudioEffect`** (abstract) → **`DelayEffect`**, **`DistortionEffect`** — polymorphism. The synthesizer just calls `effect.apply(buffer, sample_rate)` on each one without knowing the implementation. Adding a new effect means writing one class with one method.

**`SheetMusicPanel`** (extends `tk.Canvas`) — maps notes to staff positions using a diatonic step system (C=0 through B=6, ignoring accidentals for Y placement). Determines note head shape from duration (hollow for half/whole, filled for quarter and shorter). Automatically beams consecutive eighth/sixteenth notes. Handles ledger lines for notes outside the staff.

**`extract_midi_data()`** in `play_midi.py` — the controller function. Reads MIDI events, integrates delta times into absolute timestamps, pairs `note_on` with `note_off` to compute durations, builds and returns a `Score`.

**`MidiToWavGUI`** — Tkinter app that ties everything together. Runs synthesis in a background daemon thread to keep the UI responsive. All UI updates from the worker thread go through `root.after()` because Tkinter is not thread-safe.

## Volume levels and clipping

Square and sawtooth waves have higher RMS energy than sine waves at the same amplitude. To keep things from clipping when you mix multiple notes, the engine applies different volume scaling:
- Sine: 0.3
- Square / Saw: 0.15

If you're getting distorted output on dense MIDI files with lots of simultaneous notes, the mix buffer might be exceeding [-1, 1] before quantisation. The hard limiter in `_buffer_to_bytes()` clamps it, but you'll hear it. Lowering velocity or the volume adjustment constants would help.

## Music theory notes (for the notation renderer)

- B4 sits on the middle line of the treble staff. Notes on or below B4 get stems pointing up; notes above B4 get stems pointing down. This is standard engraving practice.
- The `reference_beat` parameter (default 0.5s, i.e. 120 BPM) determines how durations map to note shapes: `duration / reference_beat` gives a coefficient. Coefficient 4 = whole note, 2 = half, 1 = quarter, 0.5 = eighth, 0.25 = sixteenth.
- Consecutive beamable notes (eighth or shorter) are grouped and connected with polygon beams rather than individual flags. The beam renderer runs as a second pass after all note heads are drawn.
- Solfège notation is supported throughout: Do, Re, Mi, Fa, Sol, La, Si (with accidentals like Sol#, Mib).

## Known limitations

- **Performance**: the synthesis loop is pure Python, sample-by-sample. A 90-second MIDI file with hundreds of notes takes a few seconds to render. Vectorising with NumPy would make it near-instant, but we wanted to keep the physics explicit and readable.
- **Mono only**: single-channel output. No stereo panning.
- **Linear ADSR**: real instruments have exponential attack/release curves. Ours is linear for simplicity.
- **No sustain pedal**: MIDI sustain (CC64) messages are ignored. Notes end at their `note_off` event.
- **Sheet music is basic**: no time signatures, bar lines, or key signatures. It renders a single melodic line on a treble clef.

## If you want to test / review

```bash
# 1. Engine sanity check
cd 1st_ver
python music_engine.py
# → should produce test_mix.wav (C major chord)

# 2. MIDI batch conversion
python play_midi.py
# → reads house_at_pooh_corner.mid, outputs 3 WAV variants

# 3. GUI
python gui_enhance_test_khoa.py
# → try Acoustics Lab with: C4:0.5 D4:0.5 E4:1.0 G4:2.0
# → try loading a MIDI file in the MIDI Converter tab
# → try toggling distortion + echo, changing oscillator type
```

Things we'd appreciate feedback on:
- Does the GUI flow make sense? Anything confusing?
- How does the audio quality sound? Any unexpected clicks or artefacts?
- Is the sheet music notation readable and correct?
- Any crashes or error messages we should know about?
- Ideas for features that would actually be useful?

## Troubleshooting

**"ModuleNotFoundError: No module named 'mido'"** — run `pip install mido`. If you're using a virtual environment, make sure it's activated.

**Audio sounds harsh or clipped** — this usually means too many notes are overlapping and the mix buffer is saturating. Try lowering velocity values or the `vol_adj` constants in `_mix_note()`.

**GUI doesn't open** — make sure `matplotlib` and `tkinter` are installed. On some Linux distros, tkinter needs a separate package (`sudo apt install python3-tk`).

**Sheet music looks wrong** — check that your melody format is correct: `NoteName:Duration` separated by spaces. Example: `C4:0.5 E4:0.5 G4:1.0`. The note name must end with an octave digit.

**MIDI file produces no output** — the parser only handles `note_on` and `note_off` messages. If your MIDI file uses unusual control messages or has no standard note events, it might return an empty Score.

## What could come next

- NumPy vectorisation for the synthesis loop (10-100x speedup)
- FM synthesis and wavetable oscillators
- FFT spectral analysis view alongside the Piano Roll
- Stereo output with per-note panning
- Real-time MIDI input from a USB keyboard
- Preset save/load for synthesis configurations