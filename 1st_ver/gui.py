import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from play_midi import extract_midi_data


class MidiToWavGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MIDI → WAV Synthétiseur")
        self.root.geometry("420x260")
        self.root.resizable(False, False)

        self.midi_path = tk.StringVar()
        self.oscillator = tk.StringVar(value="sine")

        self.create_widgets()

    def create_widgets(self):
        # --- Title ---
        title = tk.Label(
            self.root,
            text="Conversion MIDI → WAV",
            font=("Arial", 14, "bold")
        )
        title.pack(pady=10)

        # --- MIDI file selection ---
        frame_file = tk.Frame(self.root)
        frame_file.pack(pady=10)

        tk.Label(frame_file, text="Fichier MIDI :").grid(row=0, column=0, sticky="w")

        entry = tk.Entry(frame_file, textvariable=self.midi_path, width=30)
        entry.grid(row=1, column=0, padx=5)

        browse_btn = tk.Button(frame_file, text="Parcourir", command=self.browse_midi)
        browse_btn.grid(row=1, column=1, padx=5)

        # --- Oscillator choice ---
        frame_osc = tk.Frame(self.root)
        frame_osc.pack(pady=10)

        tk.Label(frame_osc, text="Type d’oscillateur :").grid(row=0, column=0, sticky="w")

        osc_menu = ttk.Combobox(
            frame_osc,
            textvariable=self.oscillator,
            values=["sine", "square", "saw"],
            state="readonly",
            width=15
        )
        osc_menu.grid(row=1, column=0)
        osc_menu.current(0)

        # --- Generate button ---
        generate_btn = tk.Button(
            self.root,
            text="Générer le fichier WAV",
            font=("Arial", 11),
            command=self.generate_audio
        )
        generate_btn.pack(pady=20)

        # --- Status label ---
        self.status_label = tk.Label(self.root, text="", fg="green")
        self.status_label.pack()

    def browse_midi(self):
        filename = filedialog.askopenfilename(
            title="Choisir un fichier MIDI",
            filetypes=[("MIDI files", "*.mid")]
        )
        if filename:
            self.midi_path.set(filename)

    def generate_audio(self):
        midi_file = self.midi_path.get()
        instrument = self.oscillator.get()

        if not midi_file:
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier MIDI.")
            return

        self.status_label.config(text="Conversion en cours...")

        score = extract_midi_data(midi_file, instrument)
        if score:
            score.save_to_wav()
            self.status_label.config(
                text=f"Conversion terminée ✔ ({instrument})"
            )
        else:
            self.status_label.config(text="Erreur lors de la conversion.", fg="red")


# --- Main ---
if __name__ == "__main__":
    root = tk.Tk()
    app = MidiToWavGUI(root)
    root.mainloop()
