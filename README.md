# 🎵 MusicScore QuOM

> **Transform MIDI files into custom synthesized audio with your choice of waveforms, effects, and visual music notation.**

A Python synthesizer that reads MIDI files and generates WAV audio with customizable oscillators, ADSR envelopes, polyphonic mixing, and a visual sheet music display. Perfect for musicians, students, and audio enthusiasts exploring sound synthesis.

---

## ✨ What Can You Do?

- 🎹 **Convert MIDI to WAV** – Generate synthesized audio from any MIDI file
- 🎛️ **Choose Your Sound** – Select from sine, square, or sawtooth waveforms
- 🎚️ **Fine-Tune Parameters** – Adjust attack, release, distortion, and echo effects
- 📊 **See & Hear Together** – Visualize melodies on a treble clef staff in real-time
- 🎼 **Proper Music Notation** – Correct stem directions, note head styles, and beam grouping (following music theory)
- 🎸 **Polyphonic Synthesis** – Mix multiple simultaneous notes seamlessly

---

## 🚀 Quick Start (60 seconds)

### Requirements
- Python 3.x (e.g., Python 3.13)
- Virtual environment (recommended)

### Step 1: Install Dependencies
From the project root directory:
```bash
pip install mido matplotlib
```

### Step 2: Test the Engine
Generate a simple test WAV file:
```bash
cd 1st_ver
python music_engine.py
```
✅ You should see: `Done! Saved test_mix.wav`

### Step 3: Launch the GUI (Optional)
Interactively create and synthesize melodies:
```bash
python gui_enhance_test_khoa.py
```
This opens a GUI with two tabs:
- **MIDI Converter** – Load a `.mid` file and generate audio
- **Acoustics Lab** – Type a melody (e.g., `C4:0.5 E4:0.5 G4:1.0`) and hear it instantly

---

## 📁 Project Structure

```
MusicScore_QuOM/
├── README.md                        # This file
├── house_at_pooh_corner.mid        # Example MIDI file
│
├── 1st_ver/                         # Main source code
│   ├── music_engine.py              # Core: Note, Synthesizer, Score classes
│   ├── play_midi.py                 # MIDI parsing → audio synthesis
│   ├── sheet_music.py               # Music notation & visualization
│   ├── gui_enhance_test_khoa.py     # Main interactive GUI
│   │
│   └── examples/                    # Legacy/alternative implementations
│       ├── gui.py                   # Simple basic GUI
│       └── gui_staff.py             # Composer demo
│
└── [Generated Files]
    └── *.wav                        # Output audio files
```

---

## 🎯 How It Works (Beginner-Friendly)

```
MIDI File
    ↓
[play_midi.py] ← Parse notes, timing, and velocity
    ↓
[Score Object] ← Organize notes onto a timeline
    ↓
[Synthesizer] ← Generate waveforms + apply ADSR envelope
    ↓
[Effect Rack] ← Optional: Distortion & Delay
    ↓
[Mixing] ← Combine all notes into one audio stream
    ↓
[WAV File] ← 16-bit PCM audio saved to disk
```

### Key Classes Explained

| Class | What It Does | Example |
|-------|-------------|---------|
| **Note** | Represents one musical note | `Note.from_name("C4", start_time=0, duration=0.5)` |
| **Synthesizer** | Generates audio waveforms with effects | `synth.oscillator = "sine"`, `synth.add_effect(DelayEffect())` |
| **Score** | Container for all notes + WAV export | `score.add_note(note)`, `score.save_to_wav()` |
| **SheetMusicPanel** | Visual notation display (treble clef) | Drawn in GUI automatically |

---

## 🎮 Using the GUI

### Tab 1: MIDI Converter
1. Click **"..."** to browse and select a `.mid` file
2. Choose your waveform: Sine, Square, or Saw
3. Adjust settings (attack, release, distortion, echo)
4. Click **"▶ Generate WAV"**
5. (Optional) Click **"📊 Piano Roll"** to see note distribution
6. (Optional) Click **"♫ Play"** to hear the result

### Tab 2: Acoustics Lab
1. In the text field, type a melody using this format:
   ```
   Note:Duration Note:Duration Note:Duration
   ```
   - **Note**: `C4`, `D4#`, `E4`, `Fab4`, etc. (English or Solfège names OK)
   - **Duration**: Seconds (e.g., `0.5` = 500ms, `1.0` = 1 second)
   
2. Example: `C4:0.5 E4:0.5 G4:1.0 REST:0.25 C5:1.0`
   - Plays C, then E, then G (longer), a silence, then high C

3. See the sheet music update in real-time
4. Click **"▶ Generate WAV"** to synthesize and save

---

## 📚 Learning Resources

### Understanding Music Notation (in the output)
- **Hollow (white) note heads** = long notes (half notes, whole notes)
- **Filled (black) note heads** = short notes (quarter notes, eighths, sixteenths)
- **Stems** = vertical lines extending from note heads
  - **Up** = notes on or below middle line (B4)
  - **Down** = notes above middle line (B4)
- **Beams** = horizontal lines connecting multiple short notes (standard notation)
- **Ledger lines** = small lines for notes outside the staff

### Sound Design Tips
1. **Sine waves** = smooth, pure tone (default)
2. **Square waves** = buzz-like, digital sound
3. **Sawtooth waves** = bright, harsh sound
4. **Attack (0.01s)** = sudden onset (plucked sound)
5. **Release (0.1s)** = slow fade-out (piano sound)
6. **Distortion** = adds harmonics (guitar-like tone)
7. **Delay/Echo** = reverb effect (spacious feel)

### Example Commands
```bash
# Generate test audio with overlapping notes
python 1st_ver/music_engine.py

# Convert a MIDI file for all waveforms
python 1st_ver/play_midi.py

# Run the GUI
python 1st_ver/gui_enhance_test_khoa.py
```

---

## 🔧 Technical Details

### Time Units
- **All times are in seconds** (floats)
- MIDI timing is accumulated from delta-time to absolute time in `play_midi.py`
- Reference beat (GUI tab 2) = 0.5 seconds = one quarter note at 120 BPM

### Oscillator Volume
Carefully tuned to prevent clipping:
- Sine: 0.3 amplitude
- Square/Saw: 0.15 amplitude
- Adjust if mixing multiple layers

### Music Theory in Code
- **B4** = treble clef middle line (step_diff = 4)
- Stems UP for notes on/below B4; DOWN for above
- Consecutive eighths/sixteenths auto-beam (via `draw_melody_with_beaming()`)
- Accidentals (#, b) supported in all note names

---

## ✅ Recent Improvements

- ✨ **Refactored Note class** to dataclass with `Note.from_name()` factory + caching
- 🎵 **Fixed stem direction** to follow standard music theory
- 📦 **Added beam grouping** for proper eighth/sixteenth notation
- 🧹 **Removed dead code** (duplicate GUIs, unused imports)
- 🎯 **Cleaner module organization** with helpers in `examples/`

---

## 🤝 Feedback & Contributing

**We'd love your input!** Please test and let us know:
- ✉️ Does the GUI feel intuitive?
- 🔊 Does the audio sound good? Any distortion or clicks?
- 🎼 Is the sheet music readable and accurate?
- 🐛 Any bugs or crashes?
- 💡 Feature requests?

### Testing Checklist
```bash
# 1. Engine test (expects test_mix.wav)
python 1st_ver/music_engine.py

# 2. GUI test (load example MIDI)
python 1st_ver/gui_enhance_test_khoa.py
# → Try "Acoustics Lab" with: C4:0.5 D4:0.5 E4:1.0

# 3. MIDI conversion (expect _sine.wav, _square.wav, _saw.wav)
python 1st_ver/play_midi.py
```

---

## 📖 File Reference

| File | Purpose | For Whom |
|------|---------|----------|
| `music_engine.py` | Core synthesis engine | Developers, sound designers |
| `play_midi.py` | MIDI parsing + synthesis pipeline | Developers, batch processing |
| `sheet_music.py` | Music notation rendering | Developers, UI fans |
| `gui_enhance_test_khoa.py` | Interactive GUI | Everyone! 🎉 |
| `examples/gui.py` | Simple alternative GUI | Reference/learning |

---

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| Audio sounds distorted/clipped | Lower oscillator volume in `music_engine.py` or reduce note velocity |
| Hanging/stuck notes | Ensure all MIDI note_on have matching note_off |
| GUI won't launch | Check `matplotlib` is installed: `pip install matplotlib` |
| Sheet music looks wrong | Verify melody format: `C4:0.5 D4:0.5` (note name, colon, duration) |
| File not found | Check working directory: `cd 1st_ver` before running scripts |

---

## 📝 Next Steps & Ideas

- 🎹 Real-time MIDI input from USB keyboard
- 🎛️ Visual knobs for parameter control in GUI
- 💾 Save/load synthesis presets
- 🎵 Support for tempo/time signature changes
- 🔗 Combine multiple synthesizers in one track
- 🎤 Voice synthesis (experimental)

---

## 📜 License

This project is open for learning and experimentation. Please respect original MIDI compositions and artists when converting files.

---

**Enjoy creating! 🎶**

Questions? Found a bug? Have ideas? **Feedback is welcome!** Open an issue or reach out directly.
