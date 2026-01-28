import math
import wave
import struct

class Note:
    """
    Represents a musical event on a timeline.
    """
    def __init__(self, frequency, start_time, duration, velocity=0.5):
        self.frequency = frequency
        self.start_time = start_time # When does this note start? (seconds)
        self.duration = duration     # How long does it last? (seconds)
        self.velocity = velocity     # Volume (0.0 to 1.0)

    @staticmethod
    def get_freq(name):
        """Converts string (e.g., 'A4') to Hz."""
        if name == 'REST': return 0.0
        semitones = {'C':0, 'C#':1, 'Db':1, 'D':2, 'D#':3, 'Eb':3, 'E':4, 'F':5, 'F#':6, 'Gb':6, 'G':7, 'G#':8, 'Ab':8, 'A':9, 'A#':10, 'Bb':10, 'B':11}
        try:
            if len(name) == 3:
                note_str, octave = name[0:2], int(name[2])
            else:
                note_str, octave = name[0], int(name[1])
            absolute_semitone = (octave * 12) + semitones[note_str]
            return 440 * (2 ** ((absolute_semitone - 57) / 12))
        except:
            print(f"Warning: Could not parse note '{name}', defaulting to 0Hz")
            return 0.0

    @staticmethod
    def midi_to_freq(midi_number):
        """Converts MIDI note number (0-127) to Hz."""
        return 440.0 * (2 ** ((midi_number - 69) / 12))

class Synthesizer:
    """
    The Audio Engine. Renders a list of Notes into a mixed waveform.
    """
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate

    def render_track(self, notes):
        if not notes: return b''
        
        # 1. Determine total length
        last_note = max(notes, key=lambda n: n.start_time + n.duration)
        total_seconds = last_note.start_time + last_note.duration + 0.5
        total_samples = int(total_seconds * self.sample_rate)
        
        # 2. Create the Canvas (Mixing Buffer)
        print(f"Mixing {len(notes)} notes into {total_seconds:.2f}s audio...")
        mix_buffer = [0.0] * total_samples

        # 3. Paint notes
        for note in notes:
            self._mix_note(mix_buffer, note)

        # 4. Convert to Bytes
        return self._buffer_to_bytes(mix_buffer)

    def _mix_note(self, buffer, note):
        start_idx = int(note.start_time * self.sample_rate)
        dur_samples = int(note.duration * self.sample_rate)
        attack = int(self.sample_rate * 0.01) # 10ms
        release = int(self.sample_rate * 0.01)

        for i in range(dur_samples):
            if start_idx + i >= len(buffer): break
            
            # Math: Sine Wave
            t = i / self.sample_rate
            wave = math.sin(2 * math.pi * note.frequency * t)
            
            # Math: Envelope (ADSR)
            env = 1.0
            if i < attack: env = i / attack
            elif i > (dur_samples - release): env = (dur_samples - i) / release
            
            # Mixing: Add to existing value
            buffer[start_idx + i] += wave * env * note.velocity * 0.3

    def _buffer_to_bytes(self, float_buffer):
        audio_bytes = bytearray()
        for sample in float_buffer:
            # Clipping protection
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