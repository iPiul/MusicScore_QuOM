import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import platform
import subprocess

# Visualization libraries
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Your backend
from play_midi import extract_midi_data

class MidiToWavGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MIDI → WAV Synthesizer")
        self.root.geometry("450x350") # Slightly taller for new buttons
        self.root.resizable(False, False)

        self.midi_path = tk.StringVar()
        self.oscillator = tk.StringVar(value="sine")
        self.last_generated_score = None # Store score for visualization

        self.create_widgets()

    def create_widgets(self):
        # --- Title ---
        tk.Label(self.root, text="MIDI Studio Converter", font=("Arial", 16, "bold"), fg="#333").pack(pady=15)

        # --- File Section ---
        frame_file = tk.Frame(self.root)
        frame_file.pack(pady=5)
        tk.Label(frame_file, text="Source:").grid(row=0, column=0, sticky="w")
        tk.Entry(frame_file, textvariable=self.midi_path, width=35).grid(row=1, column=0, padx=5)
        tk.Button(frame_file, text="...", width=3, command=self.browse_midi).grid(row=1, column=1)

        # --- Controls Section ---
        frame_controls = tk.LabelFrame(self.root, text="Synthesizer Settings", padx=10, pady=10)
        frame_controls.pack(pady=15, fill="x", padx=20)

        # Oscillator Dropdown
        tk.Label(frame_controls, text="Waveform:").pack(side=tk.LEFT)
        osc_menu = ttk.Combobox(frame_controls, textvariable=self.oscillator, 
                                values=["sine", "square", "saw"], state="readonly", width=10)
        osc_menu.pack(side=tk.LEFT, padx=10)
        osc_menu.current(0)

        # --- Action Buttons ---
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.btn_generate = tk.Button(btn_frame, text="▶ Generate WAV", bg="#dddddd", command=self.start_generation_thread)
        self.btn_generate.pack(side=tk.LEFT, padx=5)

        self.btn_visualize = tk.Button(btn_frame, text="📊 View Piano Roll", state="disabled", command=self.open_visualizer)
        self.btn_visualize.pack(side=tk.LEFT, padx=5)

        self.btn_play = tk.Button(btn_frame, text="♫ Play Audio", state="disabled", command=self.play_audio)
        self.btn_play.pack(side=tk.LEFT, padx=5)

        # --- Status ---
        self.status_label = tk.Label(self.root, text="Ready", fg="grey", font=("Arial", 9))
        self.status_label.pack(side=tk.BOTTOM, pady=5)

    def browse_midi(self):
        filename = filedialog.askopenfilename(filetypes=[("MIDI files", "*.mid")])
        if filename: self.midi_path.set(filename)

    def start_generation_thread(self):
        """Starts conversion in a separate thread to prevent freezing."""
        if not self.midi_path.get():
            messagebox.showwarning("Warning", "Please select a MIDI file first.")
            return

        # Disable button to prevent double-clicks
        self.btn_generate.config(state="disabled", text="Processing...")
        self.status_label.config(text="Converting... (Please wait)", fg="blue")
        
        # Launch Thread
        threading.Thread(target=self.generate_audio_logic, daemon=True).start()

    def generate_audio_logic(self):
        """The heavy lifting happens here."""
        try:
            midi_file = self.midi_path.get()
            instrument = self.oscillator.get()

            # Call backend
            score = extract_midi_data(midi_file, instrument)
            
            if score:
                score.save_to_wav()
                self.last_generated_score = score # Save for visualization
                
                # Update GUI (Must be done safely)
                self.root.after(0, self.on_conversion_success)
            else:
                self.root.after(0, lambda: self.on_conversion_error("Extraction failed"))

        except Exception as e:
            self.root.after(0, lambda: self.on_conversion_error(str(e)))

    def on_conversion_success(self):
        self.status_label.config(text="Success! WAV file created.", fg="green")
        self.btn_generate.config(state="normal", text="▶ Generate WAV")
        self.btn_visualize.config(state="normal") # Enable Visualization
        self.btn_play.config(state="normal")      # Enable Play

    def on_conversion_error(self, error_msg):
        self.status_label.config(text=f"Error: {error_msg}", fg="red")
        self.btn_generate.config(state="normal", text="▶ Generate WAV")

    def play_audio(self):
        """Opens the generated WAV file with the system default player."""
        if not self.last_generated_score: return
        wav_path = self.last_generated_score.name
        
        try:
            if platform.system() == 'Windows':
                os.startfile(wav_path)
            elif platform.system() == 'Darwin': # macOS
                subprocess.call(('open', wav_path))
            else: # Linux
                subprocess.call(('xdg-open', wav_path))
        except Exception as e:
            messagebox.showerror("Error", f"Could not open player: {e}")

    def open_visualizer(self):
        """Opens a new window with the Matplotlib graph."""
        if not self.last_generated_score: return

        # Create new top-level window
        viz_window = tk.Toplevel(self.root)
        viz_window.title(f"Piano Roll - {self.last_generated_score.name}")
        viz_window.geometry("800x600")

        # Create Matplotlib Figure
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # --- Plotting Logic (Reuse from before) ---
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

        # Embed into Tkinter Window
        canvas = FigureCanvasTkAgg(fig, master=viz_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = MidiToWavGUI(root)
    root.mainloop()