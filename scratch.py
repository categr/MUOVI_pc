import os
import tarfile

current_dir = os.path.dirname(os.path.abspath(__file__))

# Definisci il percorso relativo alla cartella di estrazione
extraction_dir = os.path.join(current_dir, '..', 'extraction_pc')

# Assicurati che la directory di estrazione esista, altrimenti creala
if not os.path.exists(extraction_dir):
    os.makedirs(extraction_dir)

# data folder
data_dir = ('C:\\Users\\catec\\Desktop\\Simulazione_MUOVI\\FILE_MUOVI')

# Percorso del file tar
tar_file_path = os.path.join(data_dir, 'test Muovi tibiale.tar')

with tarfile.open(tar_file_path, 'r') as tar:
    tar.extractall(path=extraction_dir)
