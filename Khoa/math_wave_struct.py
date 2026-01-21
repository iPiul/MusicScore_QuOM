import math
import wave
import struct

class Note:
    """
    Represents a single musical note.
    """
    def __init__(self, frequency, duration, amplitude=0.5):
        self.frequency = frequency  # In Hertz (Hz)
        self.duration = duration    # In Seconds
        self.amplitude = amplitude  # 0.0 to 1.0 (Volume)

    @staticmethod
    def get_freq(name):
        """
        Converts a note name (e.g., 'A4', 'C#5', 'Bb3') to frequency in Hz.
        Reference: A4 = 440Hz
        """
        if name == 'REST':
            return 0.0
            
        # 1. Define the order of notes in an octave
        # We map note names to their semitone index (C is 0, B is 11)
        semitones = {
            'C': 0, 'C#': 1, 'Db': 1, 
            'D': 2, 'D#': 3, 'Eb': 3, 
            'E': 4, 
            'F': 5, 'F#': 6, 'Gb': 6, 
            'G': 7, 'G#': 8, 'Ab': 8, 
            'A': 9, 'A#': 10, 'Bb': 10, 
            'B': 11
        }

        # 2. Parse the string (separate Letter/Accidental from Octave)
        # Example: "C#4" -> note_str="C#", octave=4
        if len(name) == 3:
            note_str = name[0:2] # e.g. "C#"
            octave = int(name[2])
        else:
            note_str = name[0]   # e.g. "C"
            octave = int(name[1])

        # 3. Calculate distance from A4
        # A4 is at index 9 in octave 4.
        
        # Calculate absolute semitone number (C0 = 0)
        absolute_semitone = (octave * 12) + semitones[note_str]
        
        # Calculate semitones relative to A4 (A4 is note 57 in absolute terms)
        # A4 = (4 * 12) + 9 = 57
        n = absolute_semitone - 57
        
        # 4. Apply the formula
        frequency = 440 * (2 ** (n / 12))
        return frequency

class Synthesizer:
    """
    Responsible for turning Note data into raw audio bytes.
    """
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate

    def generate_wave(self, note: Note):
        """Generates the raw audio data for a specific note."""
        audio = []
        num_samples = int(note.duration * self.sample_rate)
        
        # Max amplitude for 16-bit audio is 32767. 
        # We scale note.amplitude by this number.
        volume = 32767.0 * note.amplitude

        for i in range(num_samples):
            # The Math: sin(2 * pi * frequency * time)
            # time = i / sample_rate
            value = volume * math.sin(2 * math.pi * note.frequency * (i / self.sample_rate))
            
            # Pack the number into a binary 16-bit integer (short)
            # '<h' means little-endian short integer
            packed_value = struct.pack('<h', int(value))
            audio.append(packed_value)
            
        return b''.join(audio)

class Score:
    """
    Represents a collection of notes, handles file creation, 
    and interprets string melodies.
    """
    def __init__(self, name="output.wav"):
        self.notes = []
        self.name = name
        self.synth = Synthesizer()

    def add_note(self, note: Note):
        self.notes.append(note)

    def play_melody(self, melody_string):
        """
        Parses a string of notes and adds them to the score.
        Format: "NoteName:Duration NoteName:Duration"
        Example: "C4:0.5 D4:0.5 E4:1.0"
        """
        # 1. Split the string by spaces to get individual note tokens
        # "C4:0.5 D4:0.5" -> ["C4:0.5", "D4:0.5"]
        tokens = melody_string.split()

        for token in tokens:
            # 2. Split each token by the colon
            parts = token.split(':')
            
            # Extract name and duration
            note_name = parts[0]
            duration = float(parts[1]) # Convert string "0.5" to float 0.5
            
            # 3. Convert name to Frequency using our Note helper
            freq = Note.get_freq(note_name)
            
            # 4. Create the Note object and add it
            new_note = Note(freq, duration)
            self.add_note(new_note)

    def save_to_wav(self):
        """Compiles all notes and writes to a WAV file."""
        print(f"Generating sound data for {len(self.notes)} notes...")
        wav_file = wave.open(self.name, 'w')
        wav_file.setparams((1, 2, 44100, 0, 'NONE', 'not compressed'))

        for note in self.notes:
            raw_data = self.synth.generate_wave(note)
            wav_file.writeframes(raw_data)

        wav_file.close()
        print(f"Done! Saved to {self.name}")

# --- implementation Instructions ---

if __name__ == "__main__":
    # 1. Create the Score
    my_song = Score("twinkle.wav")

    # 2. Define the melody as a string
    # Format: Note:Duration
    # C4:0.5 means "Play C4 for half a second"
    twinkle_melody = (
        "C4:0.5 C4:0.5 G4:0.5 G4:0.5 A4:0.5 A4:0.5 G4:1.0 "
        "F4:0.5 F4:0.5 E4:0.5 E4:0.5 D4:0.5 D4:0.5 C4:1.0"
    )

    # 3. Parse and Play
    my_song.play_melody(twinkle_melody)

    # 4. Save
    my_song.save_to_wav()