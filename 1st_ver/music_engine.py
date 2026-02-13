import math
import wave
import struct

class Note:
    """
    Data structure representing a distinct musical event in the time domain.
    """
    def __init__(self, frequency, start_time, duration, velocity=0.5):
        self.frequency = frequency  # Pitch in Hz
        self.start_time = start_time  # Absolute start time in seconds
        self.duration = duration      # Duration in seconds
        self.velocity = velocity      # Amplitude scalar (0.0 to 1.0)

    @staticmethod
    def parse_note(name):
        """
        Parses a note string into its components.
        Example: "C#4" -> ("C", "#", 4)
        Example: "Solb5" -> ("Sol", "b", 5)
        
        Returns:
            (base_name, accidental, octave) or (None, None, None)
        """
        if name == 'REST': 
            return "REST", "", 0
            
        try:
            # 1. Extract Octave (Last character)
            # We assume the last character is always the octave number (0-9)
            octave = int(name[-1])
            raw_note = name[:-1] # Everything before the number
            
            # 2. Extract Accidental
            if raw_note.endswith('#') or raw_note.endswith('b'):
                accidental = raw_note[-1]
                base_name = raw_note[:-1]
            else:
                accidental = ""
                base_name = raw_note
                
            return base_name, accidental, octave
            
        except (ValueError, IndexError):
            print(f"Warning: Could not parse note '{name}'")
            return None, None, None

    @staticmethod
    def get_freq(name):
        """
        Converts Scientific Pitch Notation (e.g., 'A4', 'C#5', 'Do4') to Hz.
        """
        if name == 'REST': return 0.0
        
        # Unified Dictionary (English + Solfège)
        semitones = {
            # English
            'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 
            'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11,
            # Solfège
            'Do': 0, 'Do#': 1, 'Reb': 1, 'Re': 2, 'Re#': 3, 'Mib': 3, 'Mi': 4, 
            'Fa': 5, 'Fa#': 6, 'Solb': 6, 'Sol': 7, 'Sol#': 8, 'Lab': 8, 'La': 9, 'La#': 10, 'Sib': 10, 'Si': 11
        }

        try:
            # Use our own helper to parse!
            base, acc, octave = Note.parse_note(name)
            
            if base is None: return 0.0
            
            # Reconstruct key for lookup (e.g., "C" + "#" = "C#")
            full_note = base + acc
            
            # Formula
            absolute_semitone = (octave * 12) + semitones[full_note]
            return 440 * (2 ** ((absolute_semitone - 57) / 12))
        except Exception as e:
            print(f"Error converting '{name}': {e}")
            return 0.0

    @staticmethod
    def midi_to_freq(midi_number):
        """Converts MIDI note index (0-127) to Frequency (Hz)."""
        return 440.0 * (2 ** ((midi_number - 69) / 12))


class AudioEffect:
    """Abstract base class for Signal Processing modules (DSP)."""
    def apply(self, buffer, sample_rate):
        raise NotImplementedError("Subclasses must implement apply()")


class DelayEffect(AudioEffect):
    """
    Implements a Feedback Delay (Echo).
    Superimposes a time-shifted copy of the signal onto itself.
    """
    def __init__(self, delay_seconds=0.5, decay=0.5):
        self.delay_seconds = delay_seconds
        self.decay = decay 

    def apply(self, buffer, sample_rate):
        delay_samples = int(self.delay_seconds * sample_rate)
        # Create a copy to read original data while writing to the buffer
        original_audio = list(buffer) 
        
        for i in range(len(buffer)):
            if i >= delay_samples:
                delayed_signal = original_audio[i - delay_samples]
                buffer[i] += delayed_signal * self.decay


class DistortionEffect(AudioEffect):
    """
    Implements Hard Clipping.
    Simulates signal saturation by capping amplitude at a threshold.
    """
    def __init__(self, drive=0.5):
        self.drive = drive # 0.0 to 1.0

    def apply(self, buffer, sample_rate):
        threshold = 1.0 - self.drive
        for i in range(len(buffer)):
            # Hard clip the signal at +/- threshold
            if buffer[i] > threshold:
                buffer[i] = threshold
            elif buffer[i] < -threshold:
                buffer[i] = -threshold
            
            # Normalize volume
            buffer[i] /= threshold


class Synthesizer:
    """
    The Audio Engine. 
    Handles waveform generation, superposition of notes, and mixing.
    """
    def __init__(self, sample_rate=44100, oscillator="sine", attack=0.01, release=0.1):
        self.sample_rate = sample_rate
        self.oscillator = oscillator 
        self.attack_time = attack   # Physics: Rise time (Transient response)
        self.release_time = release # Physics: Decay time (Damping)
        self.effects = [] 

    def add_effect(self, effect: AudioEffect):
        self.effects.append(effect)

    def render_track(self, notes):
        """
        Compiles a list of Note objects into raw PCM audio data.
        """
        if not notes: return b''
        
        # Determine total audio duration including decay tail
        last_note = max(notes, key=lambda n: n.start_time + n.duration)
        total_seconds = last_note.start_time + last_note.duration + 0.5
        total_samples = int(total_seconds * self.sample_rate)
        
        # Allocate mixing buffer (The "Canvas")
        mix_buffer = [0.0] * total_samples

        # Superposition: Add each note's wave to the buffer
        for note in notes:
            self._mix_note(mix_buffer, note)

        # Apply DSP effects chain
        for effect in self.effects:
            effect.apply(mix_buffer, self.sample_rate)

        # Quantize and encode to bytes
        return self._buffer_to_bytes(mix_buffer)

    def _mix_note(self, buffer, note):
        """Generates samples for a single note and adds them to the main buffer."""
        start_idx = int(note.start_time * self.sample_rate)
        dur_samples = int(note.duration * self.sample_rate)
        
        # Envelope settings (Transient Response)
        attack_samples = int(self.sample_rate * self.attack_time)
        release_samples = int(self.sample_rate * self.release_time)

        two_pi_f = 2 * math.pi * note.frequency

        for i in range(dur_samples):
            if start_idx + i >= len(buffer): break
            
            t = i / self.sample_rate
            
            # --- Signal Generation ---
            if self.oscillator == "sine":
                wave = math.sin(two_pi_f * t)
            elif self.oscillator == "square":
                val = math.sin(two_pi_f * t)
                wave = 1.0 if val > 0 else -1.0
            elif self.oscillator == "saw":
                # Linear ramp: 2 * (fractional_part) - 1
                wave = 2.0 * ((t * note.frequency) % 1.0) - 1.0
            else:
                wave = 0.0 

            # --- Envelope Application (ADSR) ---
            # Uses Linear Interpolation
            env = 1.0
            if i < attack_samples: 
                env = i / attack_samples
            elif i > (dur_samples - release_samples): 
                env = (dur_samples - i) / release_samples
            
            # --- Mixing ---
            # Amplitude scalar prevents clipping when summing complex waves
            vol_adj = 0.15 if self.oscillator in ["square", "saw"] else 0.3
            buffer[start_idx + i] += wave * env * note.velocity * vol_adj

    def _buffer_to_bytes(self, float_buffer):
        """Quantizes float samples (-1.0 to 1.0) to 16-bit PCM integers."""
        audio_bytes = bytearray()
        for sample in float_buffer:
            # Clamp value to prevent integer overflow
            sample = max(min(sample, 1.0), -1.0)
            audio_bytes.extend(struct.pack('<h', int(sample * 32767)))
        return audio_bytes


class Score:
    def __init__(self, name="output.wav"):
        self.notes = []
        self.name = name
        self.synth = Synthesizer()

    def add_note(self, note: Note):
        self.notes.append(note)

    def save_to_wav(self):
        raw_data = self.synth.render_track(self.notes)
        wav_file = wave.open(self.name, 'w')
        wav_file.setparams((1, 2, 44100, 0, 'NONE', 'not compressed'))
        wav_file.writeframes(raw_data)
        wav_file.close()
        print(f"Done! Saved {self.name}")

# --- EXAMPLE USAGE ---
if __name__ == "__main__":
    score = Score("test_mix.wav")
    
    # Timeline Test: Overlapping notes (Polyphony)
    # Start C4 at 0.0s
    score.add_note(Note(Note.get_freq("C4"), start_time=0.0, duration=2.0))
    # Start E4 at 0.5s (Overlaps!)
    score.add_note(Note(Note.get_freq("E4"), start_time=0.5, duration=2.0))
    # Start G4 at 1.0s (Full Chord!)
    score.add_note(Note(Note.get_freq("G4"), start_time=1.0, duration=2.0))
    
    score.save_to_wav()