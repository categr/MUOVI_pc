import os
import tarfile
import functions

current_dir = os.path.dirname(os.path.abspath(__file__))
# Definisci il percorso relativo alla cartella di estrazione
extraction_dir = os.path.join(current_dir, '..', 'extraction_pc')
'''
#Mi assicuro che la directory di estrazione esista, altrimenti la creo
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

#function per leggere info file xml
import xml.etree.ElementTree as ET
def read_xml(file_xml):
    tree = ET.parse(file_xml)
    root = tree.getroot()
    #print(root.attrib, root.tag)
    Device_name = root.get('Name')
    N_channels = root.get('DeviceTotalChannels')
    sample_frequency = root.get('SampleFrequency')
    ad_bits = root.get('ad_bits')
    return sample_frequency, ad_bits

def create_bin_command_xml(sample_frequency, ad_bits):
    # Refer to the communication protocol for details about these variables:
    ProbeEN = 1  # 1 = Probe enabled, 0 = probe disabled (bit0)
    if sample_frequency == 2000:
        EMG = 1  # 1 = EMG, 0 = EEG (bit 3)
        assert ad_bits == 16, 'Incoerence between sample frequency and ad bits'
        bytes_in_sample = 2
    if sample_frequency == 500:
        EMG = 0
        assert ad_bits == 24, 'Incoerence between sample frequency and ad bits'
        bytes_in_sample = 3

    Mode0 = 0  # [00 01 10 11] = [monop monop16 impCk Test]
    Mode1 = 0
    # Mode = 0       # 0 = 32Ch Monop, 1 = 16Ch Monop, 2 = 32Ch ImpCk, 3 = 32Ch Test (bit 1 e 2)
    # control byte: 0 0 0 0 EMG Mode_bit2 Mode_bit1 ProbeEN


    # Create the command to send to Muovi
    command = 0
    if ProbeEN == 1:
        command = 0 + EMG * 8 + + Mode1 * 4 + Mode0 * 2 + 1  # conv in decimale (ProbeEN=1*2^0+ Mode*2^1)
        if Mode0 == 0 and Mode1 == 1:
            # number_of_channels = NumChanVsMode[Mode]
            number_of_channels = 38
        else:
            number_of_channels = 38

    if (
            not number_of_channels or
            not sample_frequency or
            not bytes_in_sample):
        raise Exception(
            "Could not set number_of_channels "
            "and/or and/or bytes_in_sample")

    return (integer_to_bytes(command),
            # command, #dà il comando in decimale
            number_of_channels,
            sample_frequency,
            bytes_in_sample)