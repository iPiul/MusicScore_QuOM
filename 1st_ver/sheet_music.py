"""
MusicScore QuOM - Sheet Music Visualizer
========================================
A Tkinter-based rendering engine for musical notation.

This module translates the abstract musical data (Pitch + Duration) into
standard Western Music Notation symbols (Staff, Clef, Note Heads, Stems, Beams).

Engraving Rules Implemented:
1. Pitch: Diatonic mapping to staff lines (Treble Clef).
2. Rhythm: Shape determination (Whole/Half/Quarter) based on a reference beat.
3. Grouping: Automatic beaming for consecutive 8th and 16th notes.
"""

import tkinter as tk
from music_engine import Note

class SheetMusicPanel(tk.Canvas):
    """
    A specific Canvas widget for rendering a single melodic line on a Treble Staff.
    """
    
    # --- Engraving Constants ---
    STAFF_Y_START = 60      # Vertical offset for the top line (F5)
    LINE_SPACING = 10       # Pixels between staff lines
    BASE_NOTE_SPACING = 40  # Horizontal pixels between note centers
    STEM_LENGTH = 30        # Standard height of a note stem
    BEAM_HEIGHT = 4         # Thickness of the connecting beam
    
    def __init__(self, parent, width=500, height=150, reference_beat=0.5, **kwargs):
        super().__init__(parent, width=width, height=height, bg='white', **kwargs)
        
        # The duration (in seconds) that equals a Quarter Note (beat)
        # 0.5s = 120 BPM
        self.reference_beat = reference_beat 
        
        # Mapping Note Names -> Diatonic Steps (0-6)
        # This ignores accidentals for vertical positioning (C# and C are on the same line)
        self.diatonic_map = {
            'C':0, 'D':1, 'E':2, 'F':3, 'G':4, 'A':5, 'B':6,
            'Do':0, 'Re':1, 'Mi':2, 'Fa':3, 'Sol':4, 'La':5, 'Si':6
        }
        
        # Initialize the view
        self.draw_staff()

    def draw_staff(self):
        """Renders the background: 5 lines and the G-Clef symbol."""
        self.delete("all")
        width = int(self['width'])
        
        # Draw the 5 horizontal lines
        for i in range(5):
            y = self.STAFF_Y_START + (i * self.LINE_SPACING)
            self.create_line(10, y, width-10, y, width=1, fill="black")
            
        # Draw Treble Clef (G-Clef) roughly centered on the G line (2nd line from bottom)
        self.create_text(30, self.STAFF_Y_START + 20, text="🎼", font=("Arial", 50))
        
        # Info display for the user
        self.create_text(width-60, 20, text=f"Tempo Ref: {self.reference_beat}s", 
                         font=("Arial", 8), fill="grey")

    def draw_melody(self, melody_string):
        """
        Main Entry Point: Parses a melody string and renders it with beaming.
        Format: "C4:0.5 E4:0.5"
        """
        self.draw_staff()
        
        # Reset transient state for beams
        self._pending_beams = []
        
        # 1. Parse Input
        tokens = melody_string.split()
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
            
        # 2. Analyze Rhythm for Beaming
        # (Music Theory: Consecutive short notes are connected by beams instead of flags)
        beam_groups = self._identify_beam_groups(note_data)
        
        # 3. Render Loop
        current_x = 70 # Cursor start position
        
        for idx, (note_name, duration) in enumerate(note_data):
            # Check if this note is part of a beam group
            beam_info = beam_groups.get(idx, None)
            
            # Draw the note head, stem, and necessary accidentals
            self.draw_single_note(note_name, current_x, duration, beam_info=beam_info)
            
            # Calculate spacing based on duration coefficient
            # Whole notes (4.0) get more space; 16th notes (0.25) get less.
            coef = duration / self.reference_beat
            spacing = self.BASE_NOTE_SPACING
            
            if coef >= 4.0: spacing += 20
            elif coef <= 0.5: spacing -= 5
            
            current_x += spacing
            
        # 4. Render Beams
        # Beams are drawn last because they connect multiple notes' stems
        if hasattr(self, '_pending_beams') and self._pending_beams:
            self._draw_pending_beams()
            self._pending_beams = []

    def draw_single_note(self, note_name, x, duration, beam_info=None):
        """
        Renders a single musical event.
        Logic:
        1. Calculate Y position (Pitch).
        2. Determine Head Shape (Hollow/Filled) based on Duration.
        3. Determine Stem Direction (Up/Down).
        4. Add decorations (Flags or Beam placeholders).
        """
        
        base_name, accidental, octave = Note.parse_note(note_name)
        
        # --- Handling Rests (Silences) ---
        if base_name == "REST":
            self.create_text(x, self.STAFF_Y_START + 20, text="𝄽", font=("Arial", 20))
            return

        if base_name is None: return # Invalid note string

        try:
            # --- 1. Pitch Positioning ---
            step_index = self.diatonic_map.get(base_name, 0)
            
            # Calculate absolute diatonic height (C4 is lower than D4)
            abs_step = (octave * 7) + step_index
            
            # Reference: F5 is the top line of the staff.
            # F5 index = (5 * 7) + 3 = 38
            f5_step = 38 
            step_diff = f5_step - abs_step
            
            # Convert diatonic steps to pixels (each step is half a line space)
            y_pos = self.STAFF_Y_START + (step_diff * (self.LINE_SPACING / 2))
            
            # --- 2. Rhythm & Appearance ---
            # Coefficient (C) = Duration / Beat
            # C=4: Whole, C=2: Half, C=1: Quarter, C=0.5: Eighth
            coef = duration / self.reference_beat
            
            # Rule: Whole (4.0) and Half (2.0) notes are hollow (White fill)
            is_hollow = (coef >= 2.0)
            fill_color = "white" if is_hollow else "black"
            outline_width = 2 if is_hollow else 1
            
            # Draw Note Head
            self.create_oval(x, y_pos - 5, x + 12, y_pos + 5, 
                             fill=fill_color, outline="black", width=outline_width)
            
            # --- 3. Stems ---
            # Whole notes (C >= 4.0) have no stems.
            has_stem = (coef < 4.0)
            
            if has_stem:
                # Engraving Rule: Notes on/above the middle line (B4) stem DOWN.
                # B4 is exactly the middle line. step_diff(B4) = 4.
                # Heuristic: We flip at step_diff >= 4.
                stem_up = step_diff >= 4
                
                stem_x = x + 11 if stem_up else x + 1
                stem_y_start = y_pos
                stem_y_end = y_pos - self.STEM_LENGTH if stem_up else y_pos + self.STEM_LENGTH
                
                # Draw the stem line
                self.create_line(stem_x, stem_y_start, stem_x, stem_y_end, width=1.5, fill="black")
                
                # --- 4. Flags or Beams ---
                if beam_info is None:
                    # Isolated note: Draw standard flags
                    if coef <= 0.5: # Eighth Note (1 flag)
                        self.draw_flag(stem_x, stem_y_end, stem_up, index=0)
                    if coef <= 0.25: # Sixteenth Note (2 flags)
                        offset = 8 if stem_up else -8
                        self.draw_flag(stem_x, stem_y_end + offset, stem_up, index=1)
                else:
                    # Part of a group: Register coordinates for the Beam Renderer
                    if not hasattr(self, '_pending_beams'):
                        self._pending_beams = []
                    
                    self._pending_beams.append({
                        'stem_x': stem_x,
                        'stem_y_end': stem_y_end,
                        'stem_up': stem_up,
                        'coef': coef,
                        'beam_info': beam_info
                    })

            # --- 5. Accidentals ---
            if accidental:
                self.create_text(x-10, y_pos, text=accidental, font=("Arial", 12, "bold"))
                
            # --- 6. Ledger Lines ---
            # Draw lines if note extends beyond the 5-line staff
            # Bottom line is E4 (y ~ start + 40). Top line is F5 (y = start).
            
            # High notes (Above staff)
            if y_pos <= (self.STAFF_Y_START - 10):
                ledger_y = self.STAFF_Y_START - 10
                while ledger_y >= y_pos:
                    self.create_line(x-6, ledger_y, x+18, ledger_y, width=1)
                    ledger_y -= 10
                    
            # Low notes (Below staff)
            elif y_pos >= (self.STAFF_Y_START + 50): 
                ledger_y = self.STAFF_Y_START + 50 
                while ledger_y <= y_pos:
                    self.create_line(x-6, ledger_y, x+18, ledger_y, width=1)
                    ledger_y += 10

        except Exception as e:
            print(f"Error rendering note {note_name}: {e}")

    def draw_flag(self, x, y, stem_up, index=0):
        """Draws a curved flag on the stem for isolated short notes."""
        if stem_up:
            # Curve down-right from top of stem
            self.create_line(x, y, x+6, y+4, x+8, y+15, smooth=True, width=2)
        else:
            # Curve up-right from bottom of stem
            self.create_line(x, y, x+6, y-4, x+8, y-15, smooth=True, width=2)

    # --- Beaming System ---
    
    def _identify_beam_groups(self, note_data):
        """
        Scans the melody to find consecutive 8th/16th notes that fit in a beat.
        Returns a dictionary mapping note_index -> GroupInfo.
        """
        beam_groups = {}
        current_group = []
        current_group_id = 0
        
        for idx, (note_name, duration) in enumerate(note_data):
            coef = duration / self.reference_beat
            # Is this note short enough to be beamed? (<= Eighth note)
            is_beamable = (0 < coef <= 0.5)
            
            if is_beamable:
                current_group.append(idx)
            else:
                # End of a potential group. 
                # A group must have at least 2 notes to form a beam.
                self._flush_beam_group(current_group, beam_groups, current_group_id)
                if len(current_group) >= 2: current_group_id += 1
                current_group = []
        
        # Flush any remaining notes at the end of the line
        self._flush_beam_group(current_group, beam_groups, current_group_id)
        
        return beam_groups

    def _flush_beam_group(self, group_indices, beam_dict, group_id):
        """Helper to assign group metadata to indices."""
        if len(group_indices) >= 2:
            for pos, note_idx in enumerate(group_indices):
                beam_dict[note_idx] = {
                    'group_id': group_id,
                    'position': pos,
                    'total': len(group_indices)
                }

    def _draw_pending_beams(self):
        """Iterates through pending stems and draws beams connecting them."""
        if not hasattr(self, '_pending_beams') or not self._pending_beams:
            return
        
        # 1. Organize pending stems by their Group ID
        groups = {}
        for item in self._pending_beams:
            gid = item['beam_info']['group_id']
            if gid not in groups: groups[gid] = []
            groups[gid].append(item)
        
        # 2. Draw each group
        for gid, stems in groups.items():
            if len(stems) >= 2:
                self.draw_vector_beam(stems)

    def draw_vector_beam(self, stems):
        """Draws the specific polygon for a beam group."""
        # Sort by horizontal position (Left -> Right)
        stems = sorted(stems, key=lambda s: s['stem_x'])
        
        # Determine Beam Slope
        # Simplification: We take the stem direction of the first note
        stem_up = stems[0]['stem_up']
        
        # Get coordinates of the first and last stem tips
        x1, y1 = stems[0]['stem_x'], stems[0]['stem_y_end']
        x2, y2 = stems[-1]['stem_x'], stems[-1]['stem_y_end']
        
        # Offset determines beam thickness direction
        offset = self.BEAM_HEIGHT if stem_up else -self.BEAM_HEIGHT
        
        # Draw Primary Beam (Eighth Note level)
        self.create_polygon(
            x1, y1,
            x2, y2,
            x2, y2 + offset,
            x1, y1 + offset,
            fill="black", outline="black"
        )
        
        # Draw Secondary Beam (Sixteenth Note level) if required
        # If any note in the group is a 16th note, we add a secondary line
        if any(s['coef'] <= 0.25 for s in stems):
            gap = offset * 0.6 # Visual gap between beams
            self.create_polygon(
                x1, y1 + offset,
                x2, y2 + offset,
                x2, y2 + offset + gap,
                x1, y1 + offset + gap,
                fill="black", outline="black"
            )