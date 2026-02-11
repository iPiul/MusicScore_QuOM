import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import platform
import subprocess

# Visualization libraries
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Backend integration
from play_midi import extract_midi_data
from music_engine import Score, Note, DelayEffect, DistortionEffect

class MidiToWavGUI:
    """
    Main GUI application class.
    Handles user interaction, multithreading for audio generation,
    and data visualization.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Physics Audio Lab")
        self.root.geometry("550x600") # Slightly wider for the melody input
        self.root.resizable(False, False)

        # State Variables
        self.midi_path = tk.StringVar()
        self.oscillator = tk.StringVar(value="sine")
        self.last_generated_score = None 
        
        # New: Melody String Variable
        self.melody_var = tk.StringVar(value="C4:0.5 E4:0.5 G4:1.0")

        self.create_widgets()

    def create_widgets(self):
        # Header
        tk.Label(self.root, text="Python Audio Synthesizer", font=("Arial", 16, "bold"), fg="#333").pack(pady=10)

        # --- TABS CONFIGURATION ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=5, fill="x", padx=10)

        # TAB 1: MIDI Converter
        self.tab_midi = tk.Frame(self.notebook, pady=10)
        self.notebook.add(self.tab_midi, text="  MIDI Converter  ")
        
        tk.Label(self.tab_midi, text="Source File:").grid(row=0, column=0, sticky="w", padx=10)
        tk.Entry(self.tab_midi, textvariable=self.midi_path, width=40).grid(row=0, column=1, padx=5)
        tk.Button(self.tab_midi, text="...", width=3, command=self.browse_midi).grid(row=0, column=2)

        # TAB 2: Acoustics Lab (Sequencer)
        self.tab_tone = tk.Frame(self.notebook, pady=10)
        self.notebook.add(self.tab_tone, text="  Acoustics Lab  ")
        
        frame_manual = tk.Frame(self.tab_tone)
        frame_manual.pack(fill="x", padx=10)
        
        tk.Label(frame_manual, text="Melody Sequence (Format: Note:Duration)").pack(anchor="w")
        tk.Label(frame_manual, text="Example: C4:0.5 D4:0.5 E4:1.0 REST:0.5", font=("Arial", 8), fg="grey").pack(anchor="w")
        
        # Wide entry box for typing the melody
        tk.Entry(frame_manual, textvariable=self.melody_var, width=60, font=("Consolas", 10)).pack(pady=5)

        # --- GLOBAL SETTINGS (Shared) ---
        settings_frame = tk.LabelFrame(self.root, text="Synthesizer Settings", padx=10, pady=10)
        settings_frame.pack(pady=10, fill="x", padx=20)

        # 1. Waveform Selection
        frame_wave = tk.Frame(settings_frame)
        frame_wave.pack(fill="x", pady=5)
        tk.Label(frame_wave, text="Waveform:").pack(side=tk.LEFT)
        osc_menu = ttk.Combobox(frame_wave, textvariable=self.oscillator, 
                                values=["sine", "square", "saw"], state="readonly", width=12)
        osc_menu.pack(side=tk.LEFT, padx=10)
        osc_menu.current(0)

        # 2. Physics Parameters (ADSR)
        frame_phys = tk.Frame(settings_frame)
        frame_phys.pack(fill="x", pady=10)

        tk.Label(frame_phys, text="Attack (s):").pack(side=tk.LEFT)
        self.attack_var = tk.DoubleVar(value=0.01)
        tk.Scale(frame_phys, variable=self.attack_var, from_=0.0, to=0.5, resolution=0.01, 
                 orient=tk.HORIZONTAL, length=80).pack(side=tk.LEFT, padx=5)

        tk.Label(frame_phys, text="Release (s):").pack(side=tk.LEFT)
        self.release_var = tk.DoubleVar(value=0.1)
        tk.Scale(frame_phys, variable=self.release_var, from_=0.0, to=1.0, resolution=0.05, 
                 orient=tk.HORIZONTAL, length=80).pack(side=tk.LEFT, padx=5)

        # 3. Effects Rack
        frame_fx = tk.LabelFrame(settings_frame, text="Effects Rack", padx=5, pady=5)
        frame_fx.pack(fill="x", pady=5)
        
        self.delay_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame_fx, text="Echo (Delay)", variable=self.delay_var, fg="blue").pack(side=tk.LEFT, padx=10)
        
        self.dist_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame_fx, text="Distortion (Clip)", variable=self.dist_var, fg="red").pack(side=tk.LEFT, padx=10)

        # --- Action Buttons ---
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.btn_generate = tk.Button(btn_frame, text="▶ Generate WAV", bg="#dddddd", command=self.start_generation_thread)
        self.btn_generate.pack(side=tk.LEFT, padx=5)

        self.btn_visualize = tk.Button(btn_frame, text="📊 Piano Roll", state="disabled", command=self.open_visualizer)
        self.btn_visualize.pack(side=tk.LEFT, padx=5)

        self.btn_play = tk.Button(btn_frame, text="♫ Play", state="disabled", command=self.play_audio)
        self.btn_play.pack(side=tk.LEFT, padx=5)

        # Status Bar
        self.status_label = tk.Label(self.root, text="Ready", fg="grey", font=("Arial", 9))
        self.status_label.pack(side=tk.BOTTOM, pady=5)

    def browse_midi(self):
        filename = filedialog.askopenfilename(filetypes=[("MIDI files", "*.mid")])
        if filename: self.midi_path.set(filename)

    def start_generation_thread(self):
        """Starts processing based on the active tab."""
        current_tab = self.notebook.index(self.notebook.select())
        
        if current_tab == 0: # MIDI Tab
            if not self.midi_path.get():
                messagebox.showwarning("Warning", "Please select a MIDI file first.")
                return
            target_method = self.generate_midi_logic
        else: # Acoustics Lab Tab
            target_method = self.generate_tone_logic

        self.btn_generate.config(state="disabled", text="Processing...")
        self.status_label.config(text="Converting... (Please wait)", fg="blue")
        
        threading.Thread(target=target_method, daemon=True).start()

    def _configure_score_effects(self, score):
        """Helper to apply GUI settings to any Score object."""
        score.synth.oscillator = self.oscillator.get()
        score.synth.attack_time = self.attack_var.get()
        score.synth.release_time = self.release_var.get()
        
        if self.dist_var.get():
            score.synth.add_effect(DistortionEffect(drive=0.5))
        if self.delay_var.get():
            score.synth.add_effect(DelayEffect(delay_seconds=0.3, decay=0.4))

    def generate_midi_logic(self):
        """Logic for Tab 1 (MIDI)"""
        try:
            midi_file = self.midi_path.get()
            instrument = self.oscillator.get()
            
            atk = self.attack_var.get()
            rel = self.release_var.get()
            use_dly = self.delay_var.get()
            use_dist = self.dist_var.get()

            score = extract_midi_data(midi_file, instrument, 
                                      attack=atk, release=rel, 
                                      use_delay=use_dly, use_distortion=use_dist)
            
            if score:
                score.save_to_wav()
                self.last_generated_score = score
                self.root.after(0, self.on_conversion_success)
            else:
                self.root.after(0, lambda: self.on_conversion_error("Extraction failed"))

        except Exception as e:
            self.root.after(0, lambda: self.on_conversion_error(str(e)))

    def generate_tone_logic(self):
        """Logic for Tab 2 (Manual Melody)"""
        try:
            # 1. Get Input String
            melody_str = self.melody_var.get().strip()
            if not melody_str:
                 raise ValueError("Melody cannot be empty")

            filename = f"lab_sequence_{self.oscillator.get()}.wav"
            score = Score(filename)
            
            # 2. Parse the String "C4:0.5 D4:0.5"
            tokens = melody_str.split()
            current_time = 0.0

            for token in tokens:
                if ":" in token:
                    # Split "C4:0.5" -> name="C4", duration="0.5"
                    name, dur_str = token.split(":")
                    duration = float(dur_str)
                else:
                    # Default duration if not specified
                    name = token
                    duration = 1.0

                freq = Note.get_freq(name)
                
                # Create Note and Add to Score
                # Logic: Start time is the accumulated time of previous notes
                note = Note(freq, start_time=current_time, duration=duration)
                score.add_note(note)
                
                # Advance the clock
                current_time += duration

            # 3. Apply Effects & Render
            self._configure_score_effects(score)
            score.save_to_wav()
            
            self.last_generated_score = score
            self.root.after(0, self.on_conversion_success)

        except Exception as e:
            self.root.after(0, lambda: self.on_conversion_error(str(e)))

    def on_conversion_success(self):
        self.status_label.config(text="Success! WAV file created.", fg="green")
        self.btn_generate.config(state="normal", text="▶ Generate WAV")
        self.btn_visualize.config(state="normal")
        self.btn_play.config(state="normal")

    def on_conversion_error(self, error_msg):
        self.status_label.config(text=f"Error: {error_msg}", fg="red")
        self.btn_generate.config(state="normal", text="▶ Generate WAV")

    def play_audio(self):
        if not self.last_generated_score: return
        wav_path = self.last_generated_score.name
        try:
            if platform.system() == 'Windows':
                os.startfile(wav_path)
            elif platform.system() == 'Darwin':
                subprocess.call(('open', wav_path))
            else:
                subprocess.call(('xdg-open', wav_path))
        except Exception as e:
            messagebox.showerror("Error", f"Could not open player: {e}")

    def open_visualizer(self):
        if not self.last_generated_score: return

        viz_window = tk.Toplevel(self.root)
        viz_window.title(f"Piano Roll - {self.last_generated_score.name}")
        viz_window.geometry("800x600")

        fig, ax = plt.subplots(figsize=(8, 6))
        
        score = self.last_generated_score
        starts = [n.start_time for n in score.notes]
        pitches = [n.frequency for n in score.notes]
        durations = [n.duration for n in score.notes]
        colors = [(n.velocity, 0.2, 1.0 - n.velocity) for n in score.notes]

        ax.barh(pitches, durations, left=starts, height=2.0, color=colors, edgecolor='black')
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Frequency (Hz)")
        ax.set_title("Note Distribution")
        ax.grid(True, linestyle='--', alpha=0.5)

        # Handle Auto-Scaling for Single/Few Notes
        if len(pitches) > 0:
            min_freq = min(pitches)
            max_freq = max(pitches)
            if max_freq - min_freq < 50:
                center = (max_freq + min_freq) / 2
                ax.set_ylim(center - 50, center + 50)

        canvas = FigureCanvasTkAgg(fig, master=viz_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = MidiToWavGUI(root)
    root.mainloop()