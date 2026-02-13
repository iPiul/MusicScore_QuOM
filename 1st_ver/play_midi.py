"""
MusicScore QuOM - MIDI Parser
=============================
Converts standard MIDI files (.mid) into the internal Score format.

This module handles the translation from MIDI's "Event-based" paradigm
(Note On / Note Off events at specific time deltas) to the engine's 
"Object-based" paradigm (Note objects with specific start times and durations).
"""

import mido
from music_engine import Score, Note, DelayEffect, DistortionEffect 

def extract_midi_data(midi_filename, instrument_name="sine", 
                      attack=0.01, release=0.1, 
                      use_delay=False, use_distortion=False):    
    """
    Reads a MIDI file and compiles it into a synthesizeable Score.
    
    The synthesis engine requires explicit duration for every note, but MIDI
    streams provide separate 'Start' and 'Stop' events. This function pairs 
    them up to calculate exact durations in seconds.

    Args:
        midi_filename (str): Path to the source .mid file.
        instrument_name (str): Oscillator type ('sine', 'square', 'saw').
        attack (float): Envelope attack time (transient rise) in seconds.
        release (float): Envelope release time (damping) in seconds.
        use_delay (bool): If True, adds a feedback echo effect.
        use_distortion (bool): If True, adds a hard-clipping overdrive effect.

    Returns:
        Score: A fully populated Score object, or None if the file is missing.
    """
    print(f"--- Parsing: {midi_filename} ---")
    
    try:
        # mido handles the low-level binary parsing of MIDI chunks
        midi_file = mido.MidiFile(midi_filename)
    except FileNotFoundError:
        print(f"Error: Could not find file '{midi_filename}'")
        return None
    
    # --- Output Setup ---
    # Construct a descriptive filename for the generated WAV
    # Example: song.mid -> song_sine_dist_echo.wav
    fx_suffix = ""
    if use_distortion: fx_suffix += "_dist"
    if use_delay: fx_suffix += "_echo"

    output_filename = midi_filename.replace(".mid", f"_{instrument_name}{fx_suffix}.wav")
    score = Score(output_filename)
    
    # Configure the physics of the virtual instrument
    score.synth.oscillator = instrument_name
    score.synth.attack_time = attack
    score.synth.release_time = release

    # --- Effects Chain ---
    # Signal processing order is crucial. 
    # Standard practice: Distortion (Dynamics) -> Delay (Time-based).
    if use_distortion:
        print("-> Applied Effect: Overdrive/Distortion")
        score.synth.add_effect(DistortionEffect(drive=0.5))
        
    if use_delay:
        print("-> Applied Effect: Slapback Echo")
        score.synth.add_effect(DelayEffect(delay_seconds=0.3, decay=0.4))

    # --- Event Processing Loop ---
    
    # MIDI time is stored as "Delta Time" (time elapsed since the *previous* message).
    # We must integrate these deltas to find the "Absolute Time" for our timeline.
    absolute_time_cursor = 0.0
    
    # Dictionary to track currently playing notes: { midi_note_number: start_time }
    active_notes_buffer = {} 
    notes_processed = 0
    
    # Iterate through all messages in the MIDI file (flattened across tracks)
    for msg in midi_file:
        # Advance the clock
        absolute_time_cursor += msg.time

        if msg.type == 'note_on' and msg.velocity > 0:
            # Note Start: Record the timestamp
            active_notes_buffer[msg.note] = absolute_time_cursor
            
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            # Note End: Retrieve the start timestamp to calculate duration.
            # (Note: The MIDI standard allows 'note_on' with velocity 0 to act as 'note_off')
            if msg.note in active_notes_buffer:
                start_time = active_notes_buffer.pop(msg.note)
                duration = absolute_time_cursor - start_time
                
                # Convert pitch to frequency (Hz) and add to Score
                frequency = Note.midi_to_freq(msg.note)
                new_note = Note(frequency, start_time=start_time, duration=duration)
                score.add_note(new_note)
                
                notes_processed += 1

    print(f"Extraction successful. {notes_processed} notes compiled.")
    return score

if __name__ == "__main__":
    # Internal test: Generate all waveform variations for the sample file
    test_file = "house_at_pooh_corner.mid" 
    
    print(f"Running batch conversion on {test_file}...")
    for wave_type in ["sine", "square", "saw"]:
        result = extract_midi_data(test_file, instrument_name=wave_type)
        if result:
            result.save_to_wav()