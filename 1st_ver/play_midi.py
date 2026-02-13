import mido
from music_engine import Score, Note, DelayEffect, DistortionEffect 

def extract_midi_data(midi_filename, instrument_name="sine", 
                      attack=0.01, release=0.1, 
                      use_delay=False, use_distortion=False):    
    """
    Parses a MIDI file and converts it into a Score object.
    
    Args:
        midi_filename (str): Path to the source .mid file.
        instrument_name (str): Waveform type ('sine', 'square', 'saw').
        attack (float): Envelope attack time in seconds.
        release (float): Envelope release time in seconds.

    Returns:
        Score: A populated Score object ready for synthesis.
    """
    print(f"--- Processing {midi_filename} ---")
    
    try:
        mid = mido.MidiFile(midi_filename)
    except FileNotFoundError:
        print(f"Error: File '{midi_filename}' not found.")
        return None
    
    # Initialize Score
    # We append tags to the filename so files don't overwrite each other
    fx_tag = ""
    if use_distortion: fx_tag += "_dist"
    if use_delay: fx_tag += "_echo"

    # Include effect tags in the output filename for clarity
    output_name = midi_filename.replace(".mid", f"_{instrument_name}{fx_tag}.wav")
    my_score = Score(output_name)
    
    # Configure Synthesizer parameters (Instrument & Physics)
    my_score.synth.oscillator = instrument_name
    my_score.synth.attack_time = attack
    my_score.synth.release_time = release

    # 2. Configure Effects Rack
    # Order matters! Usually, we distort first, then echo the result.
    if use_distortion:
        print("-> Adding Distortion Effect")
        # Drive=0.5 adds a nice "crunch" without destroying the sound
        my_score.synth.add_effect(DistortionEffect(drive=0.5))
        
    if use_delay:
        print("-> Adding Delay Effect")
        # 0.3s delay is a standard "slapback" echo
        my_score.synth.add_effect(DelayEffect(delay_seconds=0.3, decay=0.4))

    # --- Time Tracking ---
    # MIDI uses 'Delta Time' (time since last event).
    # We must accumulate this to get 'Absolute Time' for the timeline.
    current_time = 0.0
    active_notes = {} 
    count = 0
    
    for msg in mid:
        # Accumulate Delta Time
        current_time += msg.time

        # Handle Note On (Key Press)
        if msg.type == 'note_on' and msg.velocity > 0:
            active_notes[msg.note] = current_time
            
        # Handle Note Off (Key Release)
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            if msg.note in active_notes:
                start_t = active_notes.pop(msg.note)
                duration = current_time - start_t
                
                # Create and store the Note event
                freq = Note.midi_to_freq(msg.note)
                new_note = Note(freq, start_time=start_t, duration=duration)
                my_score.add_note(new_note)
                count += 1

    print(f"Extraction complete: {count} notes found.")
    return my_score

if __name__ == "__main__":
    # Example usage for testing without GUI
    target_file = "house_at_pooh_corner.mid" 
    
    for instrument in ["sine", "square", "saw"]:
        score = extract_midi_data(target_file, instrument_name=instrument)
        if score:
            score.save_to_wav()