## MusicScore QuOM — AI Coding Agent Guide

**Latest Update:** February 2026  
**Project Version:** 1.0  
**Status:** Active Development

This repository implements a complete MIDI→WAV synthesis pipeline with support for multiple oscillators, ADSR envelopes, and polyphonic audio mixing. All code is located in the `1st_ver/` directory.

---

## Documentation

**Start here:** Read [README.md](../../README.md) for a comprehensive project overview, installation instructions, and user guide.

This copilot guide supplements the README with technical details for AI agents working on the codebase.

---

## Core Files Reference

### Primary Implementation Files
- **[1st_ver/music_engine.py](1st_ver/music_engine.py)** — Core synthesis engine
  - `Note` class: frequency, start_time, duration, velocity
  - `Synthesizer` class: oscillator rendering (sine, square, saw), ADSR envelope generation
  - `Score` class: note container with WAV export functionality
  
- **[1st_ver/play_midi.py](1st_ver/play_midi.py)** — MIDI parsing and conversion
  - `extract_midi_data()`: parses MIDI files, accumulates relative times to absolute times
  - Handles both `note_off` and `note_on` (velocity=0) for note termination
  - Converts MIDI note numbers to Hz frequencies
  
- **[house_at_pooh_corner.mid](house_at_pooh_corner.mid)** — Example MIDI asset for testing

### Optional UI/Testing
- **[1st_ver/gui.py](1st_ver/gui.py)** — Basic GUI (minimal, not required for CLI operations)
- **[1st_ver/gui_enhance_test_khoa.py](1st_ver/gui_enhance_test_khoa.py)** — Enhanced testing and GUI variant

---

## Quick Mental Model

```
MIDI File → play_midi.extract_midi_data()
           ↓
        Score + Notes
           ↓
Synthesizer.render_track(score)
           ↓
Mixed Audio Buffer (float, clamped to [-1.0, 1.0])
           ↓
Score.save_to_wav() → 16-bit WAV File
```

---

## Essential Technical Details

### Time Representation
- **All times are floating-point seconds** — not samples or MIDI ticks
- MIDI `msg.time` is relative delta; `play_midi.py` accumulates to absolute times
- Maintain this convention when refactoring or adding features

### Note Representation
```python
Note(frequency, start_time, duration, velocity=0.5)
# frequency: in Hz (use Note.midi_to_freq() for conversion)
# start_time: absolute time in seconds
# duration: note length in seconds
# velocity: 0.0–1.0 amplitude scaling
```

### Oscillators & Volume Scaling
- **Sine wave**: volume factor ≈ **0.3**
- **Square wave**: volume factor ≈ **0.15**
- **Sawtooth wave**: volume factor ≈ **0.15**
- Use conservative factors to prevent clipping; test audio output

### ADSR Envelope
- **Attack**: ~0.01s (rise to peak)
- **Decay**: ~0.01s (settle to sustain)
- **Sustain**: held amplitude level
- **Release**: ~0.01s (fade to silence after note ends)
- Short durations minimize clicking/popping artifacts on brief notes

### Polyphonic Mixing
- Multiple notes are rendered separately as float buffers
- Buffers summed element-wise into a single master buffer
- Master buffer clamped to [-1.0, 1.0] to prevent overflow
- Clamped values packed as 16-bit signed integers (struct format `h`)

### MIDI Note-off Handling
- **Both** `note_off` messages and `note_on` with velocity=0 terminate notes
- When modifying MIDI parsing, ensure both are processed correctly
- Log total note count and verify every `note_on` has a matching `note_off` or velocity==0

---

## Running & Testing

### Quick Commands

From the workspace root:
```bash
cd 1st_ver
python music_engine.py     # Generate test_mix.wav with example synthesis
python play_midi.py        # Convert ../house_at_pooh_corner.mid → WAV files
```

### What to Expect
- `music_engine.py`: Creates `test_mix.wav` (example with mixed oscillators)
- `play_midi.py`: Generates separate WAV files for each detected oscillator type
- Both should complete without errors and produce audible output

---

## Dependencies

- **External**: `mido==1.2.3+` (MIDI file parsing)
- **Standard Library**: `math`, `wave`, `struct`, `os`, `sys`

Install: `pip install mido`

---

## Project Conventions

### Frequency Representation
- **Always work with Hz internally** — do not store or process MIDI note numbers in render logic
- Use `Note.midi_to_freq()` when converting from MIDI
- Keep frequency as `float` throughout processing

### Silence & Rests
- Represented by frequency = **0.0**
- Treated as zero amplitude (no waveform generation)
- Useful for gaps between notes without creating audio dropouts

### Adding New Waveforms
When adding a new oscillator type:
1. Add `elif` branch in `Synthesizer` waveform selector (follow existing pattern)
2. Choose conservative volume factor (typically 0.1–0.3)
3. Test for clipping by listening to output and checking max sample values
4. Document the volume factor in this guide

---

## Files to Check When Making Changes

| Purpose | File |
|---------|------|
| Oscillators & ADSR | [1st_ver/music_engine.py](1st_ver/music_engine.py) |
| MIDI parsing & note handling | [1st_ver/play_midi.py](1st_ver/play_midi.py) |
| Testing & GUI | [1st_ver/gui_enhance_test_khoa.py](1st_ver/gui_enhance_test_khoa.py) |
| Example MIDI | [house_at_pooh_corner.mid](house_at_pooh_corner.mid) |
| User documentation | [README.md](../../README.md) |

---

## Editing Guidelines for AI Agents

### Refactoring & Changes
1. **Preserve time units** — All times must remain in seconds; update buffer-length calculations accordingly if `sample_rate` changes
2. **Sample rate consistency** — `Synthesizer(sample_rate=44100, ...)` must match WAV output sample rate
3. **Per-oscillator scaling** — Adjust volume per waveform, not globally, to avoid unexpected clipping

### MIDI Handling
- Log total note count when parsing
- Verify every `note_on` has a matching `note_off` or `velocity==0`
- Accumulate MIDI deltas to maintain absolute timing

### Testing Changes
- Always generate test output: `python 1st_ver/music_engine.py`
- Listen for audio artifacts: clicks, pops, or distortion indicate ADSR/volume issues
- Check printed diagnostics: note counts, frequency ranges, timing accuracy

---

## PR & Commit Checklist

Before submitting changes:
- [ ] Run `python 1st_ver/music_engine.py` → verify `test_mix.wav` is generated
- [ ] Run `python 1st_ver/play_midi.py` → check note count and WAV output
- [ ] Listen to generated audio for clipping/distortion
- [ ] If clipping present: lower oscillator scale factors and re-test
- [ ] Verify time units (seconds) throughout code
- [ ] Update relevant comments if conventions change

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Clipping/distortion in output | Oscillator volume too high | Lower scale factor (0.3→0.2, 0.15→0.1) |
| Hanging notes / no note-off | MIDI parsing not handling velocity=0 | Check `play_midi.py` handles both `note_off` and `note_on(velocity=0)` |
| Missing audio | Empty score or zero frequencies | Log note list; verify MIDI file has valid notes |
| Clicking/popping | ADSR envelope too long for short notes | Reduce attack/release (≈0.01s is default) |

---

## Future Enhancements

Potential improvements documented in [README.md](../../README.md#future-enhancements):
- Support for multiple simultaneous waveforms in single render
- Pitch bend and control change (CC) message handling
- Real-time audio playback
- GUI parameter tuning interface
- Additional filters and effects

---

## Questions & Clarifications

If this guide is incomplete, needs clarification, or if you want expanded coverage of:
- Detailed synthesis math
- CLI automation examples
- Unit testing framework
- Performance optimization

Please reference [README.md](../../README.md) or raise an issue in the repository.

---

**Last Updated:** February 2026  
**Maintained by:** Project Team
