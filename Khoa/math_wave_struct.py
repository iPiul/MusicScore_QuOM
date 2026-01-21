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
    Represents a collection of notes and handles file creation.
    """
    def __init__(self, name="output.wav"):
        self.notes = []
        self.name = name
        self.synth = Synthesizer()

    def add_note(self, note: Note):
        self.notes.append(note)

    def save_to_wav(self):
        """Compiles all notes and writes to a WAV file."""
        print(f"Generating sound data for {len(self.notes)} notes...")
        
        # Open a wave file for writing
        # 'w' - write mode
        wav_file = wave.open(self.name, 'w')
        
        # Set parameters: (nchannels, sampwidth, framerate, nframes, comptype, compname)
        # 1 channel (mono), 2 bytes (16-bit), 44100 Hz sample rate
        wav_file.setparams((1, 2, 44100, 0, 'NONE', 'not compressed'))

        # Generate and write each note sequentially
        for note in self.notes:
            raw_data = self.synth.generate_wave(note)
            wav_file.writeframes(raw_data)

        wav_file.close()
        print(f"Done! Saved to {self.name}")

# --- implementation Instructions ---

if __name__ == "__main__":
    # 1. Create a Score
    my_song = Score("my_music.wav")

    # 2. Define some frequencies (Notes)
    # C4 = 261.63 Hz, E4 = 329.63 Hz, G4 = 392.00 Hz
    c_major_triad = [
        Note(261.63, 0.5), # C4 for 0.5 seconds
        Note(329.63, 0.5), # E4
        Note(392.00, 0.5), # G4
        Note(523.25, 1.0)  # C5 (High C) for 1 second
    ]

    # 3. Add notes to the score
    for note in c_major_triad:
        my_song.add_note(note)

    # 4. Save the file
    my_song.save_to_wav()