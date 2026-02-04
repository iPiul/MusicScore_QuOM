## MusicScore QuOM — AI Coding Agent Guide

This repo implements a simple MIDI→WAV synthesis pipeline in `1st_ver/`. The most important files are:
- `1st_ver/music_engine.py` — core `Note`, `Synthesizer`, and `Score` logic (oscillators, ADSR, mixing).
- `1st_ver/play_midi.py` — MIDI parsing and conversion into `Score`/`Note` objects (uses `mido`).
- `1st_ver/gui.py` / `1st_ver/gui_enhance_test_khoa.py` — minimal UI/testing code (not required for CLI conversions).

Quick mental model
- MIDI file → `play_midi.extract_midi_data()` collects notes (start, duration, velocity) → `Score` holds notes → `Synthesizer.render_track()` generates per-sample audio and `Score.save_to_wav()` writes a 16-bit WAV.

Essential details agents must know
- Time units: all times are floats in seconds. MIDI `msg.time` is relative; `play_midi.py` accumulates it to absolute times.
- Notes representation: `Note(frequency, start_time, duration, velocity=0.5)`. Use `Note.get_freq()` or `Note.midi_to_freq()` to obtain Hz.
- Oscillators: `sine`, `square`, `saw` — observed volume scalings: sine ≈ 0.3, square/saw ≈ 0.15 to avoid clipping. Adjust cautiously.
- ADSR: attack/release are short (≈0.01s). Changes affect pop/click artifacts; keep values small for short notes.
- Mixing: polyphony is implemented by summing note buffers into a single float buffer, then clamping to [-1.0,1.0] and packing to 16-bit ints.
- Note-off: `play_midi.py` handles both `note_off` and `note_on` with velocity=0 — ensure both are considered when modifying MIDI handling.

Run & test commands
Use the `1st_ver/` scripts directly. Examples:
```bash
cd 1st_ver
python play_midi.py        # converts house_at_pooh_corner.mid → WAVs (one per oscillator)
python music_engine.py     # runs the small example to create test_mix.wav
```

Dependencies
- `mido` (MIDI parsing). Standard libs: `math`, `wave`, `struct`.

Project-specific conventions
- Work primarily with Hz internally — do not store MIDI note numbers in render logic.
- Silence/rests are represented by frequency `0.0` and treated as zero amplitude during rendering.
- When adding waveforms, follow existing pattern in `music_engine.py` (add an `elif` branch in the oscillator switching and choose a conservative volume factor).

Files & places to look when making changes
- Oscillators + ADSR: [1st_ver/music_engine.py](1st_ver/music_engine.py)
- MIDI extraction, polyphony handling: [1st_ver/play_midi.py](1st_ver/play_midi.py)
- Example GUI/test runner: [1st_ver/gui_enhance_test_khoa.py](1st_ver/gui_enhance_test_khoa.py)
- Example MIDI asset: [house_at_pooh_corner.mid](house_at_pooh_corner.mid)

Editing guidance for agents
- Preserve time units (seconds) and sample-rate handling when refactoring. `Synthesizer` accepts a `sample_rate` parameter — update all buffer-length calculations consistently.
- Avoid global volume changes — prefer per-oscillator scaling to prevent unexpected clipping across the mix.
- When adjusting MIDI parsing, add unit-like checks: log total note count and ensure every `note_on` has a matching `note_off` (or velocity==0) to avoid hanging notes.

Quick checklist for PRs
- Run `python 1st_ver/music_engine.py` to confirm `test_mix.wav` is generated.
- Run `python 1st_ver/play_midi.py` and check the printed note count and generated WAV files.
- Listen for clipping/distortion; if present, lower oscillator scale factors.

If anything in this guide seems incomplete or you want a different level of detail (examples, more CLI automation, or unit tests), tell me which area to expand and I'll iterate.
