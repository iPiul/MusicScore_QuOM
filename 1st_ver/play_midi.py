import mido
import sys
from music_engine import Score, Note 

def extract_midi_data(midi_filename, instrument_name="sine", attack=0.01, release=0.1):
    """
    Reads a MIDI file and converts it into a Score object.
    """
    print(f"--- Loading {midi_filename} ---")
    
    # 1. Open the MIDI file
    try:
        mid = mido.MidiFile(midi_filename)
    except FileNotFoundError:
        print(f"Error: Could not find file '{midi_filename}'")
        return None

    # 2. Create your Score
    # We name the output file based on the input name
    output_name = midi_filename.replace(".mid", f"_{instrument_name}.wav")
    my_score = Score(output_name)
    my_score.synth.oscillator = instrument_name

    # Configure the synth with the physics parameters
    my_score.synth.oscillator = instrument_name
    my_score.synth.attack_time = attack
    my_score.synth.release_time = release

    # 3. The Extraction Logic
    # We must track "absolute time" (total seconds elapsed)
    current_time = 0.0
    
    # We must track which notes are currently being held down
    # Dictionary: { note_number: start_timestamp }
    active_notes = {} 

    count = 0
    
    # Iterate through every message in the MIDI file
    for msg in mid:
        # Update the clock
        # msg.time is the "wait time" since the last event
        current_time += msg.time

        # Check for "Note On" (Key Pressed)
        # Note: Some MIDI files use 'note_on' with velocity 0 to mean 'off'
        if msg.type == 'note_on' and msg.velocity > 0:
            # Store the start time for this specific note number
            active_notes[msg.note] = current_time
            
        # Check for "Note Off" (Key Released)
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            if msg.note in active_notes:
                # We found the matching start time!
                start_t = active_notes.pop(msg.note)
                duration = current_time - start_t
                
                # Convert MIDI number (0-127) to Frequency (Hz)
                freq = Note.midi_to_freq(msg.note)
                
                # Create the Note object
                new_note = Note(freq, start_time=start_t, duration=duration)
                my_score.add_note(new_note)
                count += 1

    print(f"Successfully extracted {count} notes.")
    return my_score

# --- Main Execution ---
if __name__ == "__main__":
    # You can change this filename to whatever MIDI file you downloaded
    target_file = "house_at_pooh_corner.mid" 
    
    # Run the extractor
    # Try all three instruments!
    for instrument in ["sine", "square", "saw"]:
        print(f"\nGenerating {instrument} version...")
        score = extract_midi_data(target_file, instrument_name=instrument)
        if score:
            score.save_to_wav()