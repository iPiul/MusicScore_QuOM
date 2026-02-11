import tkinter as tk
from tkinter import ttk

class Staff:
    
    def __init__(self,canvas):
        self.canvas=canvas
        self.draw_staff()
        
    def draw_staff(self):
        y0=80    # Début de la portée
        spacing=10    # Espacement entre les lignes
        for i in range (5):
            self.canvas.create_line((50,y0+i*spacing),(350,y0+i*spacing),width=2)
    

class Add_Note:
    
    NOTE_POSITIONS = {
        "Ré": 120,
        "Mi": 115,
        "Fa": 110,
        "Sol": 105,
        "La": 100,
        "Si": 95,
        "Do": 90,
        "Ré_2": 85,
        "Mi_2" : 80,
        "Fa_2" : 75
    }
    
    def __init__(self,canvas):
        self.canvas=canvas
        self.note_id = None
        
    def Display_Note(self,note_name):
        if self.note_id:
            self.canvas.delete(self.note_id)
        y = self.NOTE_POSITIONS[note_name]
        
                # Dessin de la note (ovale)
        self.note_id = self.canvas.create_oval((190, y), (205, y+10), fill="black")
        
class ComposerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Compositeur – Portée musicale")

        self.canvas = tk.Canvas(root, width=400, height=200, bg="white")
        self.canvas.pack(pady=10)

        # Portée
        self.staff = Staff(self.canvas)

        # Notes
        self.note_manager = Add_Note(self.canvas)

        # Menu déroulant
        self.note_var = tk.StringVar(value="Ré")
        notes = list(Add_Note.NOTE_POSITIONS.keys())

        
        menu = ttk.Combobox(root,textvariable=self.note_var,values=notes,state="readonly")
        menu.pack()
        
        # Bouton
        btn = tk.Button(root, text="Afficher la note", command=self.add_note)
        btn.pack(pady=10)
    
    def add_note(self):
        note = self.note_var.get()
        self.note_manager.Display_Note(note)


# --- Main ---
if __name__ == "__main__":
    root = tk.Tk()
    app = ComposerGUI(root)
    root.mainloop()