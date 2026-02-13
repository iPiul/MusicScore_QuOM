import tkinter as tk
from music_engine import Note # Connect to the Core Engine

class SheetMusicPanel(tk.Canvas):
    """
    A Canvas that draws musical notes dynamically based on text input.
    Now supports Rhythmic Notation (Whole, Half, Quarter, Eighth, Sixteenth).
    """
    def __init__(self, parent, width=500, height=150, reference_beat=0.5, **kwargs):
        super().__init__(parent, width=width, height=height, bg='white', **kwargs)
        self.staff_y_start = 60 # Y position of the top line
        self.line_spacing = 10  # Pixels between lines
        self.base_note_spacing = 40  # Base pixels between notes
        
        # The duration (in seconds) that represents a Quarter Note (C=1.0)
        # Default 0.5s (120 BPM)
        self.reference_beat = reference_beat 
        
        # Diatonic steps map (Unified English + Solfège)
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
            
        # Draw Treble Clef Symbol
        self.create_text(30, self.staff_y_start + 30, text="🎼", font=("Arial", 30))
        
        # Debug Text for Reference T
        self.create_text(width-60, 20, text=f"T = {self.reference_beat}s", font=("Arial", 8), fill="grey")

    def draw_melody(self, melody_string):
        """Parses a string like 'C4:0.5 E4:1.0' and draws it with correct symbols."""
        self.draw_staff()
        tokens = melody_string.split()
        
        start_x = 70 # Start drawing after the clef
        
        for token in tokens:
            # 1. Extract Note Name and Duration
            if ":" in token:
                parts = token.split(":")
                note_name = parts[0]
                try:
                    duration = float(parts[1])
                except ValueError:
                    duration = 1.0
            else:
                note_name = token
                duration = 1.0 # Default if not specified

            # 2. Draw the note
            self.draw_single_note(note_name, start_x, duration)
            
            # 3. Dynamic Spacing (Give whole notes more room)
            coef = duration / self.reference_beat
            spacing = self.base_note_spacing
            if coef >= 4.0: spacing += 20
            elif coef <= 0.5: spacing -= 5
            
            start_x += spacing

    def draw_single_note(self, note_name, x, duration, beam_info=None):
        """Calculates Y position and visual style (Head, Stem, Flags or Beams)."""
        
        base_name, accidental, octave = Note.parse_note(note_name)
        
        # --- Handle Rests ---
        if base_name == "REST":
            # Simple visualization for rest
            self.create_text(x, self.staff_y_start + 20, text="𝄽", font=("Arial", 20))
            return

        if base_name is None:
            return 

        try:
            # --- 1. Position Calculation (Pitch) ---
            step_index = self.diatonic_map.get(base_name, 0)
            abs_step = (octave * 7) + step_index
            f5_step = (5 * 7) + 3 # Reference F5
            step_diff = f5_step - abs_step
            y_pos = self.staff_y_start + (step_diff * (self.line_spacing / 2))
            
            # --- 2. Duration Logic (Rhythm) ---
            # Calculate Coefficient C relative to Reference Beat T
            # Example: If T=0.5s...
            # dur=2.0s -> coef=4 (Whole)
            # dur=1.0s -> coef=2 (Half)
            # dur=0.5s -> coef=1 (Quarter)
            # dur=0.25s -> coef=0.5 (Eighth)
            coef = duration / self.reference_beat
            
            # Determine Note Head Style
            is_hollow = (coef >= 2.0) # Whole and Half notes are hollow (white)
            fill_color = "white" if is_hollow else "black"
            
            # Draw Head
            # Hollow notes need a thicker outline to be visible
            outline_width = 2 if is_hollow else 1
            self.create_oval(x, y_pos - 5, x + 12, y_pos + 5, 
                           fill=fill_color, outline="black", width=outline_width)
            
            # Determine Stem Logic
            has_stem = (coef < 4.0) # Whole notes (4.0) have NO stem
            
            if has_stem:
                # Stem Direction Rule (Music Theory):
                # B4 (middle line) is at step_diff = 4.
                # Notes on or BELOW B4 (step_diff >= 4): stem UP
                # Notes ABOVE B4 (step_diff < 4): stem DOWN
                stem_up = step_diff >= 4
                
                stem_x = x + 11 if stem_up else x + 1
                stem_y_start = y_pos
                stem_len = 30
                stem_y_end = y_pos - stem_len if stem_up else y_pos + stem_len
                
                self.create_line(stem_x, stem_y_start, stem_x, stem_y_end, width=1.5, fill="black")
                
                # --- Flags or Beams ---
                if beam_info is None:
                    # Not part of a beam group: draw individual flags
                    if coef <= 0.5: # Eighth Note (1 flag)
                        self.draw_flag(stem_x, stem_y_end, stem_up, index=0)
                    if coef <= 0.25: # Sixteenth Note (2 flags)
                        offset = 8 if stem_up else -8
                        self.draw_flag(stem_x, stem_y_end + offset, stem_up, index=1)
                else:
                    # Store beam info for later drawing (after all stems are placed)
                    if not hasattr(self, '_pending_beams'):
                        self._pending_beams = []
                    self._pending_beams.append({
                        'stem_x': stem_x,
                        'stem_y_end': stem_y_end,
                        'stem_up': stem_up,
                        'coef': coef,
                        'beam_info': beam_info
                    })

            # --- 3. Accidental (# or b) ---
            if accidental:
                self.create_text(x-10, y_pos, text=accidental, font=("Arial", 12, "bold"))
                
            # --- 4. Ledger Lines ---
            # Draw lines if note is too high or low
            if y_pos >= (self.staff_y_start + 50): # Below E4
                ledger_y = self.staff_y_start + 50 
                while ledger_y <= y_pos:
                    self.create_line(x-6, ledger_y, x+18, ledger_y, width=1)
                    ledger_y += 10
            elif y_pos <= (self.staff_y_start - 10): # Above F5
                ledger_y = self.staff_y_start - 10
                while ledger_y >= y_pos:
                    self.create_line(x-6, ledger_y, x+18, ledger_y, width=1)
                    ledger_y -= 10

        except Exception as e:
            print(f"Drawing error for {note_name}: {e}")

    def draw_flag(self, x, y, stem_up, index=0):
        """Draws a curved flag on the stem."""
        # Simple quadratic curve simulation using line segments for the flag
        if stem_up:
            # Flag goes DOWN from the top of the stem
            # Shape: )
            self.create_line(x, y, x+6, y+4, x+8, y+15, smooth=True, width=2)
        else:
            # Flag goes UP from the bottom of the stem
            self.create_line(x, y, x+6, y-4, x+8, y-15, smooth=True, width=2)

    def draw_melody_with_beaming(self, melody_string):
        """Enhanced melody drawer with automatic beam grouping for eighth/sixteenth notes."""
        self.draw_staff()
        self._pending_beams = []
        tokens = melody_string.split()
        
        # Pre-process: extract note data
        note_data = []
        for token in tokens:
            if ":" in token:
                parts = token.split(":")
                note_name = parts[0]
                try:
                    duration = float(parts[1])
                except ValueError:
                    duration = 1.0
            else:
                note_name = token
                duration = 1.0
            note_data.append((note_name, duration))
        
        # Identify beam groups
        beam_groups = self._identify_beam_groups(note_data)
        
        start_x = 70
        for idx, (note_name, duration) in enumerate(note_data):
            beam_info = beam_groups.get(idx, None)
            self.draw_single_note(note_name, start_x, duration, beam_info=beam_info)
            
            coef = duration / self.reference_beat
            spacing = self.base_note_spacing
            if coef >= 4.0: spacing += 20
            elif coef <= 0.5: spacing -= 5
            start_x += spacing
        
        # Draw beams connecting groups of stems
        if hasattr(self, '_pending_beams') and self._pending_beams:
            self._draw_pending_beams()
            self._pending_beams = []
    
    def _identify_beam_groups(self, note_data):
        """Identifies consecutive eighth/sixteenth notes that should be beamed together."""
        beam_groups = {}
        current_group = []
        current_group_id = 0
        
        for idx, (note_name, duration) in enumerate(note_data):
            coef = duration / self.reference_beat
            is_beamable = coef <= 0.5 and coef > 0  # Eighth or shorter
            
            if is_beamable:
                current_group.append(idx)
            else:
                # Flush current group if 2+ notes
                if len(current_group) >= 2:
                    for pos, note_idx in enumerate(current_group):
                        beam_groups[note_idx] = {
                            'group_id': current_group_id,
                            'position': pos,
                            'total': len(current_group)
                        }
                    current_group_id += 1
                current_group = []
        
        # Flush remaining group
        if len(current_group) >= 2:
            for pos, note_idx in enumerate(current_group):
                beam_groups[note_idx] = {
                    'group_id': current_group_id,
                    'position': pos,
                    'total': len(current_group)
                }
        
        return beam_groups
    
    def _draw_pending_beams(self):
        """Draws beams connecting the stem endpoints stored in _pending_beams."""
        if not hasattr(self, '_pending_beams') or not self._pending_beams:
            return
        
        # Group beams by group_id
        groups = {}
        for beam_item in self._pending_beams:
            group_id = beam_item['beam_info']['group_id']
            if group_id not in groups:
                groups[group_id] = []
            groups[group_id].append(beam_item)
        
        # Draw each group's beam
        for group_id, items in groups.items():
            if len(items) >= 2:
                self.draw_beam(items)
    
    def draw_beam(self, stem_items):
        """Draws a single beam connecting multiple stem endpoints."""
        if not stem_items:
            return
        
        # Sort by x position (left to right)
        stem_items = sorted(stem_items, key=lambda it: it['stem_x'])
        
        # All stems in a beam should have same direction
        stem_up = stem_items[0]['stem_up']
        
        # Get start and end stem positions
        x1, y1 = stem_items[0]['stem_x'], stem_items[0]['stem_y_end']
        x2, y2 = stem_items[-1]['stem_x'], stem_items[-1]['stem_y_end']
        
        # Beam thickness
        beam_height = 4
        
        # Draw main beam as a filled polygon (rectangle with slope)
        offset = beam_height if stem_up else -beam_height
        self.create_polygon(
            x1, y1,
            x2, y2,
            x2, y2 + offset,
            x1, y1 + offset,
            fill="black", outline="black"
        )
        
        # For sixteenth notes (coef <= 0.25), draw secondary beam offset
        if any(item['coef'] <= 0.25 for item in stem_items):
            offset2 = offset * 0.6
            self.create_polygon(
                x1, y1 + offset,
                x2, y2 + offset,
                x2, y2 + offset + offset2,
                x1, y1 + offset + offset2,
                fill="black", outline="black"
            )