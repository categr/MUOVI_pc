
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import tarfile
import xml.etree.ElementTree as ET

class GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Signal File Sender")

        # Etichetta per mostrare il file selezionato
        self.file_label = tk.Label(root, text="Seleziona un file .tar")
        self.file_label.pack(pady=10)

        # Pulsante per la selezione del file
        self.browse_button = tk.Button(root, text="Sfoglia", command=self.browse_file)
        self.browse_button.pack(pady=10)

        # Etichetta per mostrare informazioni estratte dal file
        self.info_label = tk.Label(root, text="Informazioni file")
        self.info_label.pack(pady=10)

        # Variabili per il file e il percorso selezionati
        self.selected_file = None

    def browse_file(self):
        # Usa il file dialog per selezionare un file .tar
        file_path = filedialog.askopenfilename(
            title="Seleziona il file .tar da inviare",
            filetypes=[("File TAR", "*.tar")]  # Filtra solo i file .tar
        )

        if file_path:
            self.selected_file = file_path
            # Mostra il nome del file selezionato
            self.file_label.config(text=os.path.basename(file_path))

            # Effettua l'estrazione
            self.extract_and_process_tar_file(file_path)

    def extract_and_process_tar_file(self, file_path):
        try:
            # Directory corrente e percorso di estrazione
            current_dir = os.path.dirname(os.path.abspath(__file__))
            extraction_dir = os.path.join(current_dir, '..', 'extraction_pc')

            # Mi assicuro che la directory di estrazione esista, altrimenti la creo
            if not os.path.exists(extraction_dir):
                os.makedirs(extraction_dir)

            # Estrai il file tar
            with tarfile.open(file_path, 'r') as tar:
                tar.extractall(path=extraction_dir)

            # Cerca i file .sig estratti
            files_sig = self.find_file_sig(extraction_dir)
            assert len(files_sig) == 1, "La lista non ha un solo file .sig"

            # Estrai il nome base del file .sig e verifica la presenza del file .xml
            base_name = os.path.splitext(os.path.basename(files_sig[0]))[0]
            file_xml = os.path.join(extraction_dir, f"{base_name}.xml")

            if not os.path.exists(file_xml):
                self.info_label.config(text="File .xml non trovato.")
                return

            # Leggi le informazioni dal file .xml
            sample_frequency, ad_bits = self.read_xml(file_xml)

            # Mostra le informazioni nella GUI
            info_text = f"File .sig: {files_sig[0]}\n"
            info_text += f"Frequenza di campionamento: {sample_frequency} Hz\n"
            info_text += f"AD bits: {ad_bits}"
            self.info_label.config(text=info_text)

        except Exception as e:
            # Mostra un messaggio di errore in caso di problemi
            messagebox.showerror("Errore", f"Errore durante l'estrazione o la lettura del file: {str(e)}")

    def find_file_sig(self, folder):
        # Scansiona la cartella per trovare file con estensione .sig
        files_sig = []
        for root, _, file in os.walk(folder):
            for name_file in file:
                if name_file.endswith('.sig'):
                    files_sig.append(os.path.join(root, name_file))
        return files_sig

    def read_xml(self, file_xml_path):
        # Leggi le informazioni dal file XML
        tree = ET.parse(file_xml_path)
        root = tree.getroot()
        sample_frequency = root.get('SampleFrequency')
        ad_bits = root.get('ad_bits')
        return int(sample_frequency), int(ad_bits)

# Funzione principale per eseguire la GUI
if __name__ == "__main__":
    root = tk.Tk()
    gui = GUI(root)
    root.mainloop()
