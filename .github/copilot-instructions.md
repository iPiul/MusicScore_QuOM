# MusicScore QuOM - AI Coding Agent Instructions

## Project Overview
This is a **MIDI-to-WAV synthesis engine** that converts MIDI files into playable audio using custom synthesized waveforms (sine, square, sawtooth). The codebase demonstrates real-time audio mixing and envelope processing.

## Architecture & Key Components

### Core Classes (1st_ver/music_engine.py)

**Note**: Represents a single musical event
- Constructor: `Note(frequency, start_time, duration, velocity=0.5)`
- Static methods for frequency conversion:
  - `get_freq(name)`: Parses musical notation (e.g., "A4" → 440Hz)
  - `midi_to_freq(midi_number)`: Converts MIDI note numbers (0-127) to Hz

**Synthesizer**: The audio generation engine
- Constructor: `Synthesizer(sample_rate=44100, oscillator="sine")`
- `oscillator` parameter controls waveform: "sine" (quiet, clean), "square" (bright), "saw" (harsh)
- Volume compensation: Square/saw use 0.15 scale factor vs 0.3 for sine (discovered empirically to prevent clipping)
- Key method: `render_track(notes)` → combines all notes into a single audio buffer with ADSR envelope

**Score**: High-level music container
- Holds list of Note objects
- Links to a Synthesizer instance (waveform selection happens here)
- `save_to_wav()` outputs to 44.1kHz mono WAV file

### Data Flow
```
MIDI File → play_midi.extract_midi_data() → Score (with notes) → Synth.render_track() → WAV file
```

## Critical Implementation Details

### MIDI Extraction (play_midi.py)
- **Note tracking**: Active notes tracked in dictionary `{midi_note_number: start_time}` to handle polyphony
- **Time accumulation**: MIDI msg.time is relative delay; must accumulate to get absolute time
- **Note-off handling**: Watches for both `note_off` messages AND `note_on` with velocity=0 (some DAWs use this)
- **Output naming**: Automatically appends waveform type to filename (e.g., "song_sine.wav")

### Audio Rendering (music_engine.py)
- **Mixing**: All notes added to single float buffer; polyphonic playback achieved by summing overlapping notes
- **ADSR Envelope**: Attack/Release hardcoded to 0.01s (10ms) - affects the fade in/out quality
- **Wave generation**:
  - Sine: `sin(2π × freq × t)` - clean reference tone
  - Square: Conditional on sine sign - sharp, lo-fi quality
  - Sawtooth: `2 × ((t × freq) % 1) - 1` - ramp waveform, highest harmonic content
- **Buffer clipping**: Final mix clamped to [-1.0, 1.0] then packed as 16-bit signed integers

## Developer Workflows

### Generate Audio from MIDI
```bash
cd 1st_ver
python play_midi.py
```
Converts `house_at_pooh_corner.mid` to three WAV files (one per oscillator). Outputs print note count.

### Test Synthesizer Directly
```bash
cd 1st_ver
python music_engine.py
```
Runs example usage: generates "test_mix.wav" with overlapping C-E-G chord demonstrating polyphony.

### Jupyter Exploration
- `Music.ipynb` is the notebook interface (currently has template code, not executed)
- Import pattern: `from music_engine import Score, Note`

## Key Conventions & Patterns

### Frequency Management
- Always work in Hz internally, never MIDI note numbers
- Use `Note.get_freq()` for named notes ("C4") or `Note.midi_to_freq()` for MIDI numbers
- REST/silence represented as frequency 0.0 (handled by rendering as 0 amplitude)

### Waveform Quality Trade-off
- Sine = audibly quieter but clean (0.3 vol factor)
- Square/Saw = louder due to rich harmonics (0.15 vol factor to prevent clipping)
- If adding new waveforms, experiment with 0.1-0.3 scale factors

### Timestamp Accuracy
- All times in seconds (float)
- `start_time` = when note begins; `duration` = how long it plays
- End time = `start_time + duration`

## Integration Points

### Dependencies
- `mido`: MIDI file parsing (used in play_midi.py)
- `wave`: Python stdlib for WAV file writing (used in Score.save_to_wav)
- Standard library: `math`, `struct` for signal processing

### File I/O
- **Input**: MIDI files expected in project root (default: "house_at_pooh_corner.mid")
- **Output**: WAV files saved to same directory as script
- No database integration currently (anaconda_projects/db/ is unused)

## Testing & Validation

When making changes:
1. **Frequency correctness**: Compare `Note.get_freq()` output against a tuning reference (A4 should be 440Hz)
2. **Polyphony**: Test overlapping notes in Score examples to ensure buffer mixing works
3. **Waveform quality**: Listen for distortion/clipping (adjust vol_adjustment if needed)
4. **MIDI parsing**: Verify note counts match source file and no notes are dropped/duplicated

## Common Tasks

| Task | File(s) | Key Pattern |
|------|---------|-------------|
| Add new waveform | music_engine.py `_mix_note()` | Add elif branch with wave formula, adjust vol_adjustment |
| Modify ADSR | music_engine.py lines 56-57 | Change attack/release sample counts |
| Support different sample rates | Synthesizer.__init__ | Pass sample_rate param, update render_track() |
| Extract different MIDI track | play_midi.py | Filter msg by channel before processing |
