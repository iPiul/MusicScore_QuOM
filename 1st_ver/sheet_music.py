import tkinter as tk
from music_engine import Note # Connect to the Core Engine

class SheetMusicPanel(tk.Canvas):
    """
    A Canvas that draws musical notes dynamically based on text input.
    Uses Treble Clef spacing.
    """
    def __init__(self, parent, width=500, height=150, **kwargs):
        super().__init__(parent, width=width, height=height, bg='white', **kwargs)
        self.staff_y_start = 60 # Y position of the top line
        self.line_spacing = 10  # Pixels between lines
        self.note_spacing = 40  # Pixels between notes horizontally
        
        # Diatonic steps map (Unified English + Solfège)
        # This maps the "Base Name" to a height index (0-6)
        self.diatonic_map = {
            'C':0, 'D':1, 'E':2, 'F':3, 'G':4, 'A':5, 'B':6,
            'Do':0, 'Re':1, 'Mi':2, 'Fa':3, 'Sol':4, 'La':5, 'Si':6
        }
        self.draw_staff()

    def draw_staff(self):
        """Draws the 5 lines of the treble clef."""
        self.delete("all")
        width = int(self['width'])
        
        # Draw 5 lines
        for i in range(5):
            y = self.staff_y_start + (i * self.line_spacing)
            self.create_line(10, y, width-10, y, width=1, fill="black")
            
        # Draw Treble Clef Symbol (Simplified as a letter G)
        self.create_text(20, self.staff_y_start + 30, text="🎼", font=("Arial", 30))

    def draw_melody(self, melody_string):
        """Parses a string like 'C4:0.5 E4:0.5' and draws it."""
        self.draw_staff()
        tokens = melody_string.split()
        
        start_x = 60 # Start drawing after the clef
        
        for token in tokens:
            # Parse token (e.g. "C#4:0.5" or just "C4")
            if ":" in token:
                note_name = token.split(":")[0]
            else:
                note_name = token
                
            self.draw_single_note(note_name, start_x)
            start_x += self.note_spacing

    def draw_single_note(self, note_name, x):
        """Calculates Y position using the engine's parser."""
        
        # 1. Use the shared Music Engine to parse the string
        # This ensures we support "C#4", "Do#4", "Solb5", etc. exactly like the audio engine.
        base_name, accidental, octave = Note.parse_note(note_name)
        
        if base_name == "REST":
            self.create_text(x, self.staff_y_start + 20, text="𝄽", font=("Arial", 20))
            return

        if base_name is None:
            return # Invalid note

        try:
            # 2. Calculate vertical 'Step' height
            # Treble Clef: F5 is the top line.
            
            # Map base name to 0-6 index (C=0 ... B=6)
            step_index = self.diatonic_map.get(base_name, 0)
            
            # Absolute Diatonic Height:
            # C4 = (4*7) + 0 = 28
            # F5 = (5*7) + 3 = 38
            abs_step = (octave * 7) + step_index
            
            # Reference: F5 (Top Line) -> Index 38
            f5_step = (5 * 7) + 3 
            
            # Difference in half-lines (5px)
            step_diff = f5_step - abs_step
            
            # Calculate Y pixel
            y_pos = self.staff_y_start + (step_diff * (self.line_spacing / 2))
            
            # 3. Draw Note Head
            self.create_oval(x, y_pos - 5, x + 12, y_pos + 5, fill="black")
            
            # 4. Draw Stem
            if step_diff > 5: # Low note (Stem Up)
                self.create_line(x+12, y_pos, x+12, y_pos-30, width=2)
            else: # High note (Stem Down)
                self.create_line(x, y_pos, x, y_pos+30, width=2)
                
            # 5. Draw Accidental (# or b)
            if accidental:
                self.create_text(x-10, y_pos, text=accidental, font=("Arial", 12, "bold"))
                
            # 6. Draw Ledger Lines (if note is too high or low)
            # E4 (Bottom Line) is at y = start + 40. C4 (Middle C) is below it.
            if y_pos >= (self.staff_y_start + 40 + 10): 
                ledger_y = self.staff_y_start + 50 
                while ledger_y <= y_pos:
                    self.create_line(x-5, ledger_y, x+17, ledger_y, width=1)
                    ledger_y += 10

        except Exception as e:
            print(f"Drawing error for {note_name}: {e}")