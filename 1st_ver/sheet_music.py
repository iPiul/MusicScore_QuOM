import tkinter as tk

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
        
        # Diatonic steps map (C=0, D=1, etc.)
        self.step_map = {'C':0, 'D':1, 'E':2, 'F':3, 'G':4, 'A':5, 'B':6}
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
                note_part = token.split(":")[0]
            else:
                note_part = token
                
            if note_part == "REST":
                # Draw a rest symbol
                self.create_text(start_x, self.staff_y_start + 20, text="𝄽", font=("Arial", 20))
            else:
                self.draw_single_note(note_part, start_x)
            
            start_x += self.note_spacing

    def draw_single_note(self, note_name, x):
        """Calculates Y position for a note and draws it."""
        try:
            # 1. Parse Note (e.g., "C#4")
            if len(note_name) == 3: # Sharp/Flat e.g. C#4
                letter = note_name[0]
                accidental = note_name[1]
                octave = int(note_name[2])
            else: # Natural e.g. C4
                letter = note_name[0]
                accidental = ""
                octave = int(note_name[1])
                
            # 2. Calculate vertical 'Step' height
            # Treble Clef: Bottom line is E4.
            # We map everything relative to F5 (Top line) for simpler drawing math.
            # F5 is at self.staff_y_start.
            
            # Absolute Diatonic Index:
            # C4 = (4*7) + 0 = 28
            # F5 = (5*7) + 3 = 38
            abs_step = (octave * 7) + self.step_map.get(letter.upper(), 0)
            
            # Reference: F5 (Top Line) -> Index 38
            f5_step = (5 * 7) + 3 
            
            # Difference in half-lines (5px)
            step_diff = f5_step - abs_step
            
            # Calculate Y pixel
            # Each step is half a line spacing (5px)
            y_pos = self.staff_y_start + (step_diff * (self.line_spacing / 2))
            
            # 3. Draw Note Head
            self.create_oval(x, y_pos - 5, x + 12, y_pos + 5, fill="black")
            
            # 4. Draw Stem (Up or Down depending on height)
            if step_diff > 5: # Low note (Stem Up)
                self.create_line(x+12, y_pos, x+12, y_pos-30, width=2)
            else: # High note (Stem Down)
                self.create_line(x, y_pos, x, y_pos+30, width=2)
                
            # 5. Draw Accidental (# or b)
            if accidental:
                self.create_text(x-10, y_pos, text=accidental, font=("Arial", 12, "bold"))
                
            # 6. Draw Ledger Lines (if note is too high or low)
            # E4 (Bottom Line) is at y = start + 40
            # Notes below E4 need lines. C4 is below.
            if y_pos >= (self.staff_y_start + 40 + 10): 
                # Draw lines for every step below bottom line
                ledger_y = self.staff_y_start + 50 # First ledger line
                while ledger_y <= y_pos:
                    self.create_line(x-5, ledger_y, x+17, ledger_y, width=1)
                    ledger_y += 10

        except Exception as e:
            print(f"Could not draw note {note_name}: {e}")