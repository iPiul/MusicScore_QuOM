"""
MusicScore QuOM - Main GUI Application
======================================
The user interface for the synthesis engine. 

Architecture:
- Frontend: Tkinter (Widget Toolkit)
- Visualization: Matplotlib (Piano Roll) & Custom Canvas (Sheet Music)
- Concurrency: 'threading' module prevents GUI freezing during rendering.

Key Concept: Thread Safety
Tkinter is not thread-safe. Background threads (audio rendering) must NOT 
touch UI elements directly. We use `root.after()` to schedule UI updates 
on the main thread once the background work is done.
"""

import os
import threading
import platform
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# --- Third-Party Visualization ---
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- Local Project Modules ---
from music_engine import Score, Note, DelayEffect, DistortionEffect
from play_midi import extract_midi_data
from sheet_music import SheetMusicPanel

class MidiToWavGUI:
    """
    Primary controller for the application.
    Manages the lifecycle of the window, user inputs, and audio processing jobs.
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Physics Audio Lab")
        self.root.geometry("600x750") 
        self.root.resizable(False, False)

        # --- Application State ---
        # Stores paths and user settings
        self.midi_path = tk.StringVar()
        self.oscillator = tk.StringVar(value="sine")
        self.last_generated_score = None 
        
        # Default melody for the Acoustics Lab
        self.melody_var = tk.StringVar(value="C4:0.5 E4:0.5 G4:1.0")

        self._setup_ui()

    def _setup_ui(self):
        """Constructs the widget hierarchy."""
        
        # 1. Header
        header = tk.Label(self.root, text="Python Audio Synthesizer", 
                         font=("Helvetica", 16, "bold"), fg="#333")
        header.pack(pady=15)

        # 2. Main Navigation (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=5, fill="x", padx=15)

        # Tab A: MIDI File Converter
        self.tab_midi = tk.Frame(self.notebook, pady=15)
        self.notebook.add(self.tab_midi, text="  MIDI Converter  ")
        self._build_midi_tab(self.tab_midi)

        # Tab B: Acoustics Lab (Manual Sequencer)
        self.tab_tone = tk.Frame(self.notebook, pady=15)
        self.notebook.add(self.tab_tone, text="  Acoustics Lab  ")
        self._build_lab_tab(self.tab_tone)

        # 3. Global Synthesis Settings (Shared across tabs)
        self._build_settings_panel()

        # 4. Control Bar (Buttons)
        self._build_control_bar()

        # 5. Status Bar
        self.status_label = tk.Label(self.root, text="Ready", fg="grey", font=("Arial", 9))
        self.status_label.pack(side=tk.BOTTOM, pady=5)

    def _build_midi_tab(self, parent):
        """Layout for selecting MIDI files."""
        container = tk.Frame(parent)
        container.pack()
        
        tk.Label(container, text="Source File:").grid(row=0, column=0, sticky="w", padx=5)
        
        entry = tk.Entry(container, textvariable=self.midi_path, width=45)
        entry.grid(row=0, column=1, padx=5)
        
        btn = tk.Button(container, text="Browse...", command=self.browse_midi)
        btn.grid(row=0, column=2, padx=5)

    def _build_lab_tab(self, parent):
        """Layout for the Sheet Music and Melody Input."""
        # Input Area
        input_frame = tk.Frame(parent)
        input_frame.pack(fill="x", padx=15)
        
        tk.Label(input_frame, text="Melody Sequence (Note:Duration)", font=("Arial", 10, "bold")).pack(anchor="w")
        tk.Label(input_frame, text="Example: C4:0.5 D4:0.5 E4:1.0", font=("Arial", 8), fg="#666").pack(anchor="w")
        
        entry = tk.Entry(input_frame, textvariable=self.melody_var, width=60, font=("Consolas", 11))
        entry.pack(pady=5, fill="x")

        # Sheet Music Visualization Widget
        # We pass the reference beat (0.5s) so the visualizer knows how to calculate flags/beams
        self.sheet_music = SheetMusicPanel(parent, height=140, reference_beat=0.5)
        self.sheet_music.pack(pady=10, padx=15, fill="both", expand=True)

    def _build_settings_panel(self):
        """Layout for DSP controls (Oscillator, ADSR, Effects)."""
        group = tk.LabelFrame(self.root, text="Synthesizer Configuration", padx=15, pady=10)
        group.pack(pady=10, fill="x", padx=20)

        # Row 1: Waveform Selector
        row1 = tk.Frame(group)
        row1.pack(fill="x", pady=2)
        tk.Label(row1, text="Oscillator Type:").pack(side=tk.LEFT)
        
        osc_menu = ttk.Combobox(row1, textvariable=self.oscillator, 
                                values=["sine", "square", "saw"], state="readonly", width=15)
        osc_menu.pack(side=tk.LEFT, padx=10)
        osc_menu.current(0)

        # Row 2: ADSR Envelope Sliders
        row2 = tk.Frame(group)
        row2.pack(fill="x", pady=5)

        # Attack Slider
        tk.Label(row2, text="Attack (s):").pack(side=tk.LEFT)
        self.attack_var = tk.DoubleVar(value=0.01)
        tk.Scale(row2, variable=self.attack_var, from_=0.0, to=0.5, resolution=0.01, 
                 orient=tk.HORIZONTAL, length=100).pack(side=tk.LEFT, padx=5)

        # Release Slider
        tk.Label(row2, text="Release (s):").pack(side=tk.LEFT)
        self.release_var = tk.DoubleVar(value=0.1)
        tk.Scale(row2, variable=self.release_var, from_=0.0, to=1.0, resolution=0.05, 
                 orient=tk.HORIZONTAL, length=100).pack(side=tk.LEFT, padx=5)

        # Row 3: Effects Chain
        row3 = tk.Frame(group)
        row3.pack(fill="x", pady=5)
        
        self.delay_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row3, text="Enable Echo (Delay)", variable=self.delay_var, 
                       fg="#0055aa").pack(side=tk.LEFT, padx=10)
        
        self.dist_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row3, text="Enable Overdrive (Distortion)", variable=self.dist_var, 
                       fg="#aa0000").pack(side=tk.LEFT, padx=10)

    def _build_control_bar(self):
        """Main Action Buttons."""
        frame = tk.Frame(self.root)
        frame.pack(pady=15)

        self.btn_generate = tk.Button(frame, text="▶ Render Audio", bg="#e1e1e1", 
                                      font=("Arial", 10, "bold"),
                                      command=self.start_processing_job)
        self.btn_generate.pack(side=tk.LEFT, padx=5)

        self.btn_visualize = tk.Button(frame, text="📊 View Spectrogram", 
                                       state="disabled", command=self.open_visualizer)
        self.btn_visualize.pack(side=tk.LEFT, padx=5)

        self.btn_play = tk.Button(frame, text="♫ Play Output", 
                                  state="disabled", command=self.play_audio)
        self.btn_play.pack(side=tk.LEFT, padx=5)

    # --- Interaction Logic ---

    def browse_midi(self):
        path = filedialog.askopenfilename(filetypes=[("MIDI files", "*.mid")])
        if path: self.midi_path.set(path)

    def start_processing_job(self):
        """
        Determines which tab is active and spawns a background thread 
        to handle the heavy lifting (audio rendering).
        """
        active_tab_idx = self.notebook.index(self.notebook.select())
        
        if active_tab_idx == 0: # MIDI Tab
            if not self.midi_path.get():
                messagebox.showwarning("Input Missing", "Please select a MIDI file first.")
                return
            target_function = self._job_render_midi
        else: # Acoustics Lab Tab
            target_function = self._job_render_melody

        # Lock UI to prevent spamming
        self.btn_generate.config(state="disabled", text="Rendering...")
        self.status_label.config(text="Processing audio data...", fg="blue")
        
        # Run logic in a separate thread (Daemon threads die when the app closes)
        threading.Thread(target=target_function, daemon=True).start()

    # --- Background Jobs (Run in Worker Thread) ---

    def _job_render_midi(self):
        try:
            # Gather params (safe to read TkVars from threads, but usually safer to pass values)
            # Here we read directly for simplicity.
            score = extract_midi_data(
                self.midi_path.get(), 
                self.oscillator.get(), 
                attack=self.attack_var.get(),
                release=self.release_var.get(), 
                use_delay=self.delay_var.get(), 
                use_distortion=self.dist_var.get()
            )
            
            if score:
                score.save_to_wav()
                self.last_generated_score = score
                # Schedule success callback on Main Thread
                self.root.after(0, self._on_job_success)
            else:
                self.root.after(0, lambda: self._on_job_error("MIDI Parsing failed."))

        except Exception as e:
            self.root.after(0, lambda: self._on_job_error(str(e)))

    def _job_render_melody(self):
        try:
            melody_str = self.melody_var.get().strip()
            if not melody_str: raise ValueError("Melody cannot be empty")

            # Update Sheet Music (Must happen on Main Thread)
            self.root.after(0, lambda: self.sheet_music.draw_melody(melody_str))

            # Prepare Score
            filename = f"lab_output_{self.oscillator.get()}.wav"
            score = Score(filename)
            
            # Parse Tokens
            tokens = melody_str.split()
            cursor_time = 0.0

            for token in tokens:
                # Format: "NoteName:Duration" (e.g., C4:0.5)
                if ":" in token:
                    name, dur_str = token.split(":")
                    duration = float(dur_str)
                else:
                    name = token
                    duration = 1.0

                note = Note.from_name(name, start_time=cursor_time, duration=duration)
                score.add_note(note)
                cursor_time += duration

            # Apply Settings
            score.synth.oscillator = self.oscillator.get()
            score.synth.attack_time = self.attack_var.get()
            score.synth.release_time = self.release_var.get()
            
            if self.dist_var.get():
                score.synth.add_effect(DistortionEffect(drive=0.5))
            if self.delay_var.get():
                score.synth.add_effect(DelayEffect(delay_seconds=0.3, decay=0.4))

            # Render
            score.save_to_wav()
            
            self.last_generated_score = score
            self.root.after(0, self._on_job_success)

        except Exception as e:
            self.root.after(0, lambda: self._on_job_error(str(e)))

    # --- Callbacks (Run on Main Thread) ---

    def _on_job_success(self):
        self.status_label.config(text="Render Complete! File saved.", fg="green")
        self.btn_generate.config(state="normal", text="▶ Render Audio")
        self.btn_visualize.config(state="normal")
        self.btn_play.config(state="normal")

    def _on_job_error(self, error_msg):
        self.status_label.config(text=f"Error: {error_msg}", fg="red")
        self.btn_generate.config(state="normal", text="▶ Render Audio")
        messagebox.showerror("Rendering Error", error_msg)

    # --- External Integrations ---

    def play_audio(self):
        """Launches the default system audio player."""
        if not self.last_generated_score: return
        path = self.last_generated_score.name
        
        try:
            if platform.system() == 'Windows':
                os.startfile(path)
            elif platform.system() == 'Darwin': # macOS
                subprocess.call(('open', path))
            else: # Linux
                subprocess.call(('xdg-open', path))
        except Exception as e:
            messagebox.showerror("Playback Error", f"Could not launch player: {e}")

    def open_visualizer(self):
        """Generates a Piano Roll graph using Matplotlib."""
        if not self.last_generated_score: return

        # New window for the graph
        viz_window = tk.Toplevel(self.root)
        viz_window.title(f"Visual Analysis - {self.last_generated_score.name}")
        viz_window.geometry("800x600")

        # Generate Plot
        fig, ax = plt.subplots(figsize=(8, 6))
        
        score = self.last_generated_score
        starts = [n.start_time for n in score.notes]
        pitches = [n.frequency for n in score.notes]
        durations = [n.duration for n in score.notes]
        # Color code by velocity
        colors = [(n.velocity, 0.2, 1.0 - n.velocity) for n in score.notes]

        # Draw Gantt chart style bars
        ax.barh(pitches, durations, left=starts, height=2.0, color=colors, edgecolor='black', align='center')
        
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Frequency (Hz)")
        ax.set_title("Note Distribution (Piano Roll)")
        ax.grid(True, linestyle='--', alpha=0.5)

        # Smart Scaling: Zoom in if pitch range is small
        if pitches:
            min_f, max_f = min(pitches), max(pitches)
            if (max_f - min_f) < 50:
                mid = (max_f + min_f) / 2
                ax.set_ylim(mid - 50, mid + 50)

        # Embed plot in Tkinter window
        canvas = FigureCanvasTkAgg(fig, master=viz_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = MidiToWavGUI(root)
    root.mainloop()