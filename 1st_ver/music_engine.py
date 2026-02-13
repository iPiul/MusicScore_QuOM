"""
MusicScore QuOM - Core Audio Engine
===================================
Handles the translation of musical abstractions (Notes, Scores) into 
physical audio signals (Waveforms, PCM Data) using 12-Tone Equal Temperament.

Mathematical Basis:
- Tuning: A4 = 440Hz
- Sample Rate: 44100Hz (Standard CD Quality)
- Depth: 16-bit Signed Integer PCM
"""

import math
import wave
import struct
from dataclasses import dataclass
from functools import lru_cache

# --- Constants & Tuning Standards ---

SAMPLE_RATE = 44100
BIT_DEPTH = 32767  # Max value for 16-bit signed integer (2^15 - 1)
REF_FREQ = 440.0   # A4 Reference Pitch

# Mapping note names to semitone offsets within an octave (0-11)
SEMITONES = {
    # English Notation
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4,
    'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11,
    # Solfège Notation
    'Do': 0, 'Do#': 1, 'Reb': 1, 'Re': 2, 'Re#': 3, 'Mib': 3, 'Mi': 4,
    'Fa': 5, 'Fa#': 6, 'Solb': 6, 'Sol': 7, 'Sol#': 8, 'Lab': 8, 'La': 9, 'La#': 10, 'Sib': 10, 'Si': 11
}

def _parse_note_string(name):
    """
    Parses a note string (e.g., "C#4", "Solb5") into its components.
    Returns: (base_name, accidental, octave)
    """
    if name == 'REST':
        return "REST", "", 0

    try:
        # Assumes the last character is always the octave number
        octave = int(name[-1])
        raw_note = name[:-1]

        # Check for accidentals (# or b) at the end of the note name
        if raw_note.endswith('#') or raw_note.endswith('b'):
            accidental = raw_note[-1]
            base_name = raw_note[:-1]
        else:
            accidental = ""
            base_name = raw_note

        return base_name, accidental, octave
    except (ValueError, IndexError):
        # Graceful failure for invalid strings
        return None, None, None

@lru_cache(maxsize=1024)
def name_to_freq(name: str) -> float:
    """
    Converts a note name to frequency using the standard 12-TET formula:
    f = f_ref * 2^(Δ / 12)
    
    Where Δ is the semitone distance from A4 (Index 57).
    """
    if name == 'REST':
        return 0.0

    base, acc, octave = _parse_note_string(name)
    if base is None:
        return 0.0

    full_note_key = base + acc
    try:
        # Calculate absolute semitone index (C0 = 0)
        # A4 is (4 * 12) + 9 = 57
        semitone_index = (octave * 12) + SEMITONES[full_note_key]
        
        # Apply exponential tuning formula
        return REF_FREQ * (2 ** ((semitone_index - 57) / 12))
    except KeyError:
        return 0.0

@dataclass
class Note:
    """Data model representing a single musical event."""
    frequency: float  # Hz
    start_time: float # Seconds (Absolute track time)
    duration: float   # Seconds
    velocity: float = 0.5 # Amplitude (0.0 - 1.0)

    @classmethod
    def from_name(cls, name: str, start_time: float, duration: float, velocity: float = 0.5):
        return cls(name_to_freq(name), start_time, duration, velocity)

    # Static wrappers for external utility access
    @staticmethod
    def parse_note(name): return _parse_note_string(name)

    @staticmethod
    def get_freq(name): return name_to_freq(name)

    @staticmethod
    def midi_to_freq(midi_number):
        # MIDI note 69 is A4 (440Hz)
        return REF_FREQ * (2 ** ((midi_number - 69) / 12))


# --- DSP Effects Chain ---

class AudioEffect:
    """Interface for signal processing modules."""
    def apply(self, buffer, sample_rate):
        raise NotImplementedError("Subclasses must implement apply()")

class DelayEffect(AudioEffect):
    """
    Simple Feedback Delay Line (Echo).
    """
    def __init__(self, delay_seconds=0.5, decay=0.5):
        self.delay_seconds = delay_seconds
        self.decay = decay 

    def apply(self, buffer, sample_rate):
        delay_samples = int(self.delay_seconds * sample_rate)
        # Create a read-only copy of the dry signal
        dry_signal = list(buffer) 
        
        # Add delayed copy back into the buffer
        for i in range(len(buffer)):
            if i >= delay_samples:
                buffer[i] += dry_signal[i - delay_samples] * self.decay

class DistortionEffect(AudioEffect):
    """
    Hard Clipping Distortion.
    Simulates amplifier saturation by capping signal amplitude.
    """
    def __init__(self, drive=0.5):
        self.drive = drive # 0.0 (Clean) to 0.99 (Heavy Distortion)

    def apply(self, buffer, sample_rate):
        threshold = 1.0 - self.drive
        if threshold <= 0: threshold = 0.01 # Prevent division by zero

        for i in range(len(buffer)):
            val = buffer[i]
            # Hard clip at +/- threshold
            if val > threshold:
                val = threshold
            elif val < -threshold:
                val = -threshold
            
            # Normalize to maintain perceived volume
            buffer[i] = val / threshold


# --- Synthesis Engine ---

class Synthesizer:
    def __init__(self, sample_rate=SAMPLE_RATE, oscillator="sine", attack=0.01, release=0.1):
        self.sample_rate = sample_rate
        self.oscillator = oscillator 
        
        # Linear ADSR Envelope settings
        # Attack: Time to fade in (prevents clicking at start)
        # Release: Time to fade out (mimics acoustic damping)
        self.attack_time = attack   
        self.release_time = release 
        
        self.effects = [] 

    def add_effect(self, effect: AudioEffect):
        self.effects.append(effect)

    def render_track(self, notes):
        """
        Main rendering loop. 
        Converts abstract Note objects into a summed PCM byte stream.
        """
        if not notes: return b''
        
        # Calculate total track length including the release tail of the final note
        last_note = max(notes, key=lambda n: n.start_time + n.duration)
        total_seconds = last_note.start_time + last_note.duration + self.release_time + 0.5
        total_samples = int(total_seconds * self.sample_rate)
        
        # Initialize the mixing canvas (Float array, silence = 0.0)
        # We use floats for mixing to avoid clipping until the final stage
        mix_buffer = [0.0] * total_samples

        # Additive Synthesis: Superimpose all notes onto the canvas
        for note in notes:
            self._mix_note(mix_buffer, note)

        # Post-Processing
        for effect in self.effects:
            effect.apply(mix_buffer, self.sample_rate)

        return self._buffer_to_bytes(mix_buffer)

    def _mix_note(self, buffer, note):
        """
        Generates samples for a single note and adds them to the main buffer.
        Handles Oscillator generation and ADSR envelope application.
        """
        start_idx = int(note.start_time * self.sample_rate)
        dur_samples = int(note.duration * self.sample_rate)
        
        # Pre-calculate envelope boundaries
        attack_samples = int(self.sample_rate * self.attack_time)
        release_samples = int(self.sample_rate * self.release_time)

        # Optimization: Pre-calculate angular frequency
        two_pi_f = 2 * math.pi * note.frequency

        # Waveform generation loop
        for i in range(dur_samples):
            if start_idx + i >= len(buffer): break
            
            t = i / self.sample_rate
            
            # 1. Oscillator (Signal Generator)
            if self.oscillator == "sine":
                wave_sample = math.sin(two_pi_f * t)
            elif self.oscillator == "square":
                # Sign function approximation
                wave_sample = 1.0 if math.sin(two_pi_f * t) > 0 else -1.0
            elif self.oscillator == "saw":
                # Linear ramp
                wave_sample = 2.0 * ((t * note.frequency) % 1.0) - 1.0
            else:
                wave_sample = 0.0 

            # 2. ADSR Envelope (Amplitude Shaping)
            # Uses Linear Interpolation for simplicity
            env = 1.0
            if i < attack_samples: 
                env = i / attack_samples
            elif i > (dur_samples - release_samples): 
                env = (dur_samples - i) / release_samples
            
            # 3. Mixing
            # Apply volume adjustments based on waveform energy to prevent clipping
            # Square/Saw waves have higher RMS than Sine, so we attenuate them.
            vol_adj = 0.15 if self.oscillator in ["square", "saw"] else 0.3
            
            buffer[start_idx + i] += wave_sample * env * note.velocity * vol_adj

    def _buffer_to_bytes(self, float_buffer):
        """
        Finalizing: Quantizes float samples (-1.0 to 1.0) to 16-bit PCM integers.
        """
        audio_bytes = bytearray()
        for sample in float_buffer:
            # Clamp values to [-1.0, 1.0] (Hard Limiter)
            # This prevents integer overflow artifacts if the signal is too hot
            sample = max(min(sample, 1.0), -1.0)
            
            # Scale to 16-bit range and pack as Little-Endian Signed Short ('<h')
            pcm_val = int(sample * BIT_DEPTH)
            audio_bytes.extend(struct.pack('<h', pcm_val))
            
        return audio_bytes


class Score:
    """Container for notes and file export logic."""
    def __init__(self, name="output.wav"):
        self.notes = []
        self.name = name
        self.synth = Synthesizer()

    def add_note(self, note: Note):
        self.notes.append(note)

    def save_to_wav(self):
        raw_data = self.synth.render_track(self.notes)
        
        with wave.open(self.name, 'w') as wav_file:
            # Params: (nchannels=1, sampwidth=2, framerate=44100, ...)
            wav_file.setparams((1, 2, SAMPLE_RATE, 0, 'NONE', 'not compressed'))
            wav_file.writeframes(raw_data)
            
        print(f"Export successful: {self.name}")

# --- Functional Test ---
if __name__ == "__main__":
    test_score = Score("test_mix.wav")

    print("Generating polyphonic test chord...")
    # C Major Chord (C4 - E4 - G4) with slight arpeggiation
    test_score.add_note(Note.from_name("C4", start_time=0.0, duration=2.0))
    test_score.add_note(Note.from_name("E4", start_time=0.2, duration=1.8))
    test_score.add_note(Note.from_name("G4", start_time=0.4, duration=1.6))

    test_score.save_to_wav()