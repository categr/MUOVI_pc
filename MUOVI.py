# -*- coding: utf-8 -*-

import socket
import functions
import struct
import time
import select
from tkinter import messagebox

class MUOVI():
    def __init__(self, sample_frequency):

        self.ip_address = '127.0.0.1'  # loalhost
        self.port = 54321
        self.socket_M = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.sample_frequency = sample_frequency


        connection_accepted = False  # flag
        while (not connection_accepted):
            try:
                self.socket_M.connect((self.ip_address, self.port))
                connection_accepted = True
            except:
                pass

        self.main()


    def read_new_CB(self, command):

        # controllo che il command sia lungo un solo byte
        if not isinstance(command, bytes):
            raise TypeError("Command should be bytes type")

        if len(command) != 1:
            raise ValueError("Command must contain 1 byte")

        return command
    def create_bin_command_xml(self, sample_frequency):
        # Refer to the communication protocol for details about these variables:
        ProbeEN = 1  # 1 = Probe enabled, 0 = probe disabled (bit0)
        if sample_frequency == 2000:
            EMG = 1  # 1 = EMG, 0 = EEG (bit 3)
            #assert ad_bits == 16, 'Incoerence between sample frequency and ad bits'
            bytes_in_sample = 2
        if sample_frequency == 500:
            EMG = 0
            #assert ad_bits == 24, 'Incoerence between sample frequency and ad bits'
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

        return (functions.integer_to_bytes(command),
                # command, #dà il comando in decimale
                number_of_channels,
                sample_frequency,
                bytes_in_sample)
    def Test_mode(self, EMG, bytes_in_sample, number_of_channels):
        #buffer_size = 1368 #emg 1368/2 = 684 valori, eeg 1368/3 = 456 valori per ogni vettore inviato
        if EMG == 1:
            num_cells = 684  # len buffer/2 = num_celle, num_celle/n_channels = n_cols
            n_cols = int(num_cells / number_of_channels)
        elif EMG == 0:
            num_cells = 456
            n_cols = int(num_cells / number_of_channels)

        else:
            raise ValueError("Invalid value for EMG. EMG value must be 0 or 1.")

        # Calcola il massimo valore rappresentabile su due o tre byte
        max_value = (2 ** (bytes_in_sample * 8)) - 1

        # cond
        # Aggiungi i valori al vettore incrementando da 1 fino al massimo valore rappresentabile
        current_value = 1
        cont_rampe = 0
        max_vector_length = num_cells * bytes_in_sample
        while current_value <= max_value:  # questo while ogni rampa completa inviata

            # Inizializza il vettore a empty
            vector = bytearray()

            while len(vector) < max_vector_length:  # questo while ogni vector inviato
                # Converti il valore attuale in due byte o tre byte, a seconda del numero di byte specificato
                if bytes_in_sample == 2:
                    # Utilizza 'H' per il formato unsigned short (2 byte)
                    packed_value = struct.pack('>H', current_value)
                elif bytes_in_sample == 3:
                    # Utilizzo function pack_uint24 per unsigned (3 byte)
                    packed_value = functions.pack_uint24(current_value)
                else:
                    raise ValueError("Invalid bytes_in_sample. Must be 2 or 3.")

                # Aggiungi il valore al vettore ripetendolo 38 volte (32 Ch 4Q 2Acc)
                for _ in range(number_of_channels):
                    vector.extend(packed_value)  # per aggiungere una lista a un'altra lista

                # Incrementa il valore per il prossimo ciclo
                current_value += 1
                # Verifica se il vettore ha superato la lunghezza massima consentita
                if len(vector) >= max_vector_length:
                    break
            cont_rampe += 1
            self.socket_M.send(vector)
            print('invio', cont_rampe)
            time.sleep(1 / 16)

    def send_sig_data(self, sig_file_path, bytes_in_sample, sample_frequency, number_of_channels):
        # Definisce la dimensione del buffer (1368 byte)
        buffer_size = 1368

        # Calcola quanti campioni ci sono in ogni blocco di dati
        samples_per_block = buffer_size // (bytes_in_sample * number_of_channels)

        # Calcola il tempo che deve passare tra l'invio di ciascun blocco
        # Tempo per campione (1 / frequenza di campionamento)*numero di campioni per blocco
        time_per_block = samples_per_block / sample_frequency

        flag_sending = True  # Variabile di controllo per interrompere il ciclo

        # Apri il file in modalità binaria
        with open(sig_file_path, 'rb') as f:
            while True:

                # Leggi un blocco di dati dal file (1368 byte per ciclo)
                data = f.read(buffer_size)

                # Se non ci sono più dati nel file, riporta il puntatore all'inizio
                if not data:
                    f.seek(0)
                    continue

                # Inizializza il vettore che verrà inviato
                vector = bytearray()

                # Interpreta i dati letti e impacchettali in formato 2 byte (unsigned short)
                for i in range(0, len(data), bytes_in_sample):

                    if bytes_in_sample == 2:
                        value = struct.unpack('<H', data[i:i + bytes_in_sample])[0]  #< little endian, H:Unsigned short (2 bytes, 16 bits).
                        packed_value = struct.pack('>H',value)  #> big endian
                    elif bytes_in_sample == 3:
                        byte_array = data[i:i + bytes_in_sample]
                        value = (byte_array[2] << 16) | (byte_array[1] << 8) | byte_array[0] #Little endian
                        #value = (byte_array[0] << 16) | (byte_array[1] << 8) | byte_array[2] #big endian
                        packed_value = functions.pack_uint24(value) #big endian
                    else:
                        raise ValueError("Solo valori a 2 o 3 byte sono supportati.")

                    vector.extend(packed_value)

                # Invia il vettore attraverso il socket
                self.socket_M.send(vector)

                # Aspetta un breve intervallo (1/16 di secondo) prima di inviare il prossimo blocco #CAMBIATO
                # time.sleep(1 / 16) #CAMBIATO con le due righe dopo

                # Rispetta il tempo di attesa per la frequenza di campionamento
                time.sleep(time_per_block)

                # Stampa per tenere traccia dell'invio
                print(f'Inviato blocco di {len(vector)} byte')

                # Usa select per monitorare il socket di ricezione
                readable, _, _ = select.select([self.socket_M], [], [], 0)

                # Se il socket è pronto per essere letto ( quindi se readable non è vuoto)
                if readable:
                    # Leggo il comando
                    comm_otb = self.read_new_CB(self.socket_M.recv(1))
                    # Esegui il callback passandogli il comando ricevuto
                    flag_sending = self.handle_CB(comm_otb)

                    if not flag_sending:
                        print("Ricevuto comando di STOP. Interrompo l'invio dei dati.")
                        break  # Esce dal ciclo while


    def main(self):
        comm_otb = self.read_new_CB(self.socket_M.recv(1)) # leggo comando da socket

        # comm = functions.integer_to_bytes(15)  # 15= 1111 test mode
        # or
        comm, number_of_channels, sample_frequency, bytes_in_sample = self.create_bin_command_xml(self.sample_frequency) # creo comando da lettura file locale
        if comm == comm_otb:
            self.handle_CB(comm)
        else:
            raise ValueError("Errore: Il setup del software non è coerente con i dati scelti. Cambiare il setup ")
            # TODO: problema: si fondono le finestre di errore
            # Mostra un messaggio di errore in una finestra di dialogo
            messagebox.showerror("Errore di Setup","Il setup del software non è coerente con i dati scelti. Cambiare il setup.")



    # function handling the control byte (function e non method perchè opera su un oggetto esterno alla classe: comando)
    def handle_CB(self, comm):

        bin_comm = functions.byte_to_binary(comm)
        # bin_comm[4]=EMG  # 1 = EMG, 0 = EEG (bit 3)
        # bin_comm[5]=Modebit2 # 0 = 32Ch Monop, 1 = 16Ch Monop, 2 = 32Ch ImpCk, 3 = 32Ch Test (bit 1 e 2)
        # bin_comm[6]=Modebit1
        # bin_comm[7]=ProbeEN # 1 = Probe enabled, 0 = probe disabled (bit0)

        # GO-STOP check
        if bin_comm[7] == '1':  # if GO
            print("GO")

            # EMG-EEG check
            if bin_comm[4] == '1':  # if EMG
                # function
                EMG = 1
                sample_frequency = 2000
                bytes_in_sample = 2
            else:
                EMG = 0
                sample_frequency = 500
                bytes_in_sample = 3

            # Mode check

            if bin_comm[6] + bin_comm[5] == '11':
                # 11 = Test mode. Sends ramps on all 32 channels + 6 accessory
                number_of_channels = 38

                # while True: #mettere la condizione sul controllo del tempo massimo e sul bit GO/STOP
                # ramps= self.testMode_ramp(sample_frequency, bytes_in_sample, number_of_channels)
                # multip_sig = self.multiplex_signals(number_of_channels, bytes_in_sample, ramps)
                print("test")
                self.Test_mode(EMG, bytes_in_sample, number_of_channels)

            elif bin_comm[6] + bin_comm[5] == '10':
                # 10 = Impedance check on all 32 channels + 6 accessory
                number_of_channels = 38
                print("impedence check")


            elif bin_comm[6] + bin_comm[5] == '01':
                # 01 = This option only affects EMG mode and firmware version 3.2.0 or higher. If
                # EEG is set, or previous version of firmware is used, this mode is the same as 00.
                # Monopolar mode with preamp gain is 4. 32 monopolar bioelectrical signals + 6
                # accessory signals. Resolution is 572.2 nV and range +/-18.75 mV (2)
                number_of_channels = 38
                print("16 ch")

            else:
                number_of_channels = 38  # oppure 16? NumChanVsMode = np.array([38,22,38,38])
                # 00 = Monopolar mode with preamp gain 8. 32 monopolar bioelectrical signals + 6
                # accessory signals. Resolution is 286.1 nV and range +/-9.375 mV
                print("32 ch + 6 accessories")
                file_sig = 'C:\\Users\\catec\\PycharmProjects\\MUOVI_pc\\..\\extraction_pc\\20210324142445.sig'
                self.send_sig_data(file_sig, bytes_in_sample, sample_frequency, number_of_channels)

        else:
            self.socket_M.close()
            print("STOP, il socket è stato chiuso")
            return False


# MAIN, viene istanziato in GUI.py
#if __name__ == "__main__":
    # MUOVI1 = MUOVI()

