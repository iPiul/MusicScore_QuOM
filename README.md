# MusicScore QuOM

A Python-based MIDI to WAV synthesis pipeline that converts MIDI files into audio using customizable oscillators, ADSR envelopes, and polyphonic mixing.

## Overview

MusicScore QuOM reads MIDI files and generates high-quality WAV audio using various waveforms (sine, square, sawtooth). It supports:

- **Multiple oscillators** with selectable waveforms (sine, square, saw)
- **ADSR envelopes** for realistic sound shaping (attack, decay, sustain, release)
- **Polyphonic synthesis** by mixing multiple simultaneous notes
- **Direct MIDI parsing** using the `mido` library
- **16-bit WAV output** with customizable sample rates and format

## Quick Start

### Prerequisites

- Python 3.x
- `mido` library for MIDI parsing
- Standard library modules: `math`, `wave`, `struct`

### Installation

1. Clone or download the repository:
```bash
git clone <repository-url>
cd MusicScore_QuOM
```

2. Install dependencies:
```bash
pip install mido
```

### Basic Usage

Convert a MIDI file to WAV:

```bash
cd 1st_ver
python play_midi.py
```

This reads `house_at_pooh_corner.mid` from the parent directory and generates WAV files (one per oscillator).

Run a simple synthesis example:

```bash
cd 1st_ver
python music_engine.py
```

This creates `test_mix.wav` with example notes using mixed oscillators.

## Project Structure

```
MusicScore_QuOM/
├── README.md                          # This file
├── house_at_pooh_corner.mid          # Example MIDI file
├── 1st_ver/                          # Main implementation
│   ├── music_engine.py               # Core synthesis engine (Note, Synthesizer, Score)
│   ├── play_midi.py                  # MIDI parsing and conversion to Score
│   ├── gui.py                        # Basic GUI (optional)
│   ├── gui_enhance_test_khoa.py      # Enhanced GUI/testing (optional)
│   └── __pycache__/                  # Python cache directory
├── anaconda_projects/                # Additional project files
│   └── db/
└── [other assets]
```

## How It Works

### Mental Model

1. **MIDI Parsing**: `play_midi.py` reads MIDI files using `mido` and extracts note events (pitch, start time, duration, velocity)
2. **Score Construction**: Notes are organized into a `Score` object containing `Note` instances
3. **Synthesis**: `Synthesizer.render_track()` generates audio samples using the selected oscillator and ADSR envelope
4. **Mixing**: Multiple notes are combined (polyphonic mixing) by summing their buffers
5. **WAV Output**: The final mixed audio is clamped, converted to 16-bit integers, and saved as a WAV file

### Key Components

#### `Note` Class
Represents a single musical note:
- **Parameters**: `frequency` (Hz), `start_time` (seconds), `duration` (seconds), `velocity` (0.0–1.0)
- **Methods**: `get_freq()`, `midi_to_freq()` for frequency conversion

#### `Synthesizer` Class
Generates audio samples:
- **Oscillators**: sine, square, saw with configurable volume scaling
- **ADSR Envelope**: Attack, decay, sustain, release for realistic sound shaping
- **Method**: `render_track(score)` returns audio buffer

#### `Score` Class
Container for notes and WAV export:
- **Method**: `save_to_wav(filename, synthesizer)` writes 16-bit WAV files

### Time Units

All times in the codebase are **floating-point seconds**. MIDI `msg.time` is relative and accumulated in `play_midi.py` to absolute times.

### Oscillators & Volume

Conservative volume factors to prevent clipping:
- **Sine**: ~0.3
- **Square/Saw**: ~0.15

Adjust cautiously when mixing multiple waveforms.

### ADSR Envelope

- **Attack/Release**: Short durations (~0.01s) to minimize clicking artifacts
- **Custom tuning**: Modify in `music_engine.py` for different sound character

## Important Conventions

1. **Frequency representation**: Always work with Hz internally; do not store MIDI note numbers in render logic
2. **Silence/Rests**: Represented by frequency `0.0` and treated as zero amplitude
3. **Note-off handling**: Both `note_off` messages and `note_on` with velocity=0 are supported
4. **Polyphony**: Implemented by summing note buffers into a single float buffer, then clamping to [-1.0, 1.0]

## Testing & Troubleshooting

### Generate Test Output

Run the music engine example:
```bash
python 1st_ver/music_engine.py
```

Check for `test_mix.wav` in the output.

### Convert a MIDI File

```bash
python 1st_ver/play_midi.py
```

Outputs WAV files for each oscillator type used during synthesis.

### Troubleshooting

- **Clipping/Distortion**: Lower the oscillator scale factors in `music_engine.py`
- **Hanging Notes**: Ensure all `note_on` events have matching `note_off` or `note_on` with velocity=0
- **Missing Audio**: Check that the MIDI file contains valid note events and the sample rate is set correctly

## Configuration

### Sample Rate

Default sample rate is typically 44100 Hz. Modify in `Synthesizer` instantiation if needed.

### Oscillator Selection

Edit the oscillator type in your synthesis code:
```python
synthesizer = Synthesizer(waveform='sine', sample_rate=44100)
```

Supported waveforms: `'sine'`, `'square'`, `'saw'`

## Dependencies

- **mido**: MIDI file parsing and note event extraction
- **math**: Standard mathematical functions
- **wave**: WAV file I/O
- **struct**: Binary data packing for 16-bit PCM

## Future Enhancements

Potential improvements:
- Support for multiple simultaneous oscillators in a single render
- Advanced MIDI features (pitch bend, control change messages)
- Real-time audio playback
- GUI improvements for parameter tuning
- Additional waveforms and effects

## License

[Add your license information here]

## Contributing

For code changes and improvements:
1. Test with `python 1st_ver/music_engine.py` and `python 1st_ver/play_midi.py`
2. Ensure no clipping in output audio
3. Preserve time unit consistency (seconds throughout)
4. Add unit checks for MIDI parsing (log note count, verify matching note_on/note_off)

## Questions?

Refer to the [copilot-instructions.updated.md](.github/copilot-instructions.updated.md) for detailed technical guidance.
