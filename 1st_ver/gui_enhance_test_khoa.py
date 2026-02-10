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

class MidiToWavGUI:
    """
    Main GUI application class.
    Handles user interaction, multithreading for audio generation,
    and data visualization.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("MIDI → WAV Studio (Physics Edition)")
        self.root.geometry("480x520") # Increased height for new controls
        self.root.resizable(False, False)

        # State Variables
        self.midi_path = tk.StringVar()
        self.oscillator = tk.StringVar(value="sine")
        self.last_generated_score = None 

        self.create_widgets()

    def create_widgets(self):
        # Header
        tk.Label(self.root, text="MIDI Studio Converter", font=("Arial", 16, "bold"), fg="#333").pack(pady=15)

        # File Selection Section
        frame_file = tk.Frame(self.root)
        frame_file.pack(pady=5)
        tk.Label(frame_file, text="Source:").grid(row=0, column=0, sticky="w")
        tk.Entry(frame_file, textvariable=self.midi_path, width=35).grid(row=1, column=0, padx=5)
        tk.Button(frame_file, text="...", width=3, command=self.browse_midi).grid(row=1, column=1)

        # --- Settings Container ---
        settings_frame = tk.LabelFrame(self.root, text="Synthesizer Controls", padx=10, pady=10)
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

        # Attack Slider
        tk.Label(frame_phys, text="Attack (s):").pack(side=tk.LEFT)
        self.attack_var = tk.DoubleVar(value=0.01)
        tk.Scale(frame_phys, variable=self.attack_var, from_=0.0, to=0.5, resolution=0.01, 
                 orient=tk.HORIZONTAL, length=80).pack(side=tk.LEFT, padx=5)

        # Release Slider
        tk.Label(frame_phys, text="Release (s):").pack(side=tk.LEFT)
        self.release_var = tk.DoubleVar(value=0.1)
        tk.Scale(frame_phys, variable=self.release_var, from_=0.0, to=1.0, resolution=0.05, 
                 orient=tk.HORIZONTAL, length=80).pack(side=tk.LEFT, padx=5)

        # 3. Effects Rack (NEW)
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
        """Starts conversion in a separate thread."""
        if not self.midi_path.get():
            messagebox.showwarning("Warning", "Please select a MIDI file first.")
            return

        self.btn_generate.config(state="disabled", text="Processing...")
        self.status_label.config(text="Converting... (Please wait)", fg="blue")
        
        threading.Thread(target=self.generate_audio_logic, daemon=True).start()

    def generate_audio_logic(self):
        """Collected GUI inputs and sends to backend."""
        try:
            midi_file = self.midi_path.get()
            instrument = self.oscillator.get()
            
            # Physics Params
            atk = self.attack_var.get()
            rel = self.release_var.get()
            
            # Effects Params
            use_dly = self.delay_var.get()
            use_dist = self.dist_var.get()

            # Call Backend
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

        ax.barh(pitches, durations, left=starts, height=5.0, color=colors, edgecolor='black')
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Frequency (Hz)")
        ax.set_title("Note Distribution")
        ax.grid(True, linestyle='--', alpha=0.5)

        canvas = FigureCanvasTkAgg(fig, master=viz_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = MidiToWavGUI(root)
    root.mainloop()