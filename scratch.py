import os
import tarfile

current_dir = os.path.dirname(os.path.abspath(__file__))
# Definisci il percorso relativo alla cartella di estrazione
extraction_dir = os.path.join(current_dir, '..', 'extraction_pc')
'''
# Assicurati che la directory di estrazione esista, altrimenti creala
if not os.path.exists(extraction_dir):
    os.makedirs(extraction_dir)

# data folder
data_dir = ('C:\\Users\\catec\\Desktop\\Simulazione_MUOVI\\FILE_MUOVI')

# Percorso del file tar
tar_file_path = os.path.join(data_dir, 'test Muovi tibiale.tar')

with tarfile.open(tar_file_path, 'r') as tar:
    tar.extractall(path=extraction_dir)'''

def find_file_sig(folder):
    files_sig = []
    # Scansione della cartella
    for root, _, file in os.walk(folder):
        for name_file in file:
            if name_file.endswith('.sig'):
                files_sig.append(os.path.join(root, name_file))
    return files_sig

files_sig = find_file_sig(extraction_dir)

assert len(files_sig) == 1, "La lista non ha un solo elemento"

# Nome del file .sig senza estensione
base_name = os.path.splitext(os.path.basename(files_sig[0]))[0]

# Crea il percorso completo per il file .xml
file_xml = os.path.join(extraction_dir, f"{base_name}.xml")

# Verifica se il file .xml esiste
if not os.path.exists(file_xml):
    print("File .xml non trovato")
