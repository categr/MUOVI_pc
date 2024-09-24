# -*- coding: utf-8 -*-

import socket
# import communication
import numpy as np
import functions
import struct
import time
import threading
import tarfile
import os
import local_files_functions

class MUOVI():
    def __init__(self, **kwargs):
        # super().__init__(**kwargs)
        self.ip_address = '127.0.0.1'  # loalhost
        self.port = 54321
        self.socket_M = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        connection_accepted = False  # flag
        while (not connection_accepted):
            try:
                self.socket_M.connect((self.ip_address, self.port))
                connection_accepted = True
            except:
                pass

        self.main()
        # Thread per la lettura dei comandi
        # self.command_thread = threading.Thread(target=self.main)
        # self.command_thread.daemon = True
        # self.command_thread.start()

    def read_new_CB(self, command):

        # controllo che il command sia lungo un solo byte
        if not isinstance(command, bytes):
            raise TypeError("Command should be bytes type")

        if len(command) != 1:
            raise ValueError("Command must contain 1 byte")

        return command

    def Test_mode(self, EMG, bytes_in_sample, number_of_channels):
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
    def Read_localfile(self):
        # get the current working directory
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # data folder
        data_dir = ['C:\\Users\\catec\\Desktop\\Simulazione_MUOVI\\FILE_MUOVI']

        # Percorso del file tar
        tar_file_path = os.path.join(current_dir, 'test Muovi tibiale.tar')
        return data_dir, tar_file_path


    def main(self):
        #comm = self.read_new_CB(self.socket_M.recv(1)) # leggo comando da socket
        # or
        #comm = functions.integer_to_bytes(15)  # 15= 1111 test mode
        # or
        #inserisco i path trovati con script local files functions
        file_xml = 'C:\\Users\\catec\\PycharmProjects\\MUOVI_pc\\..\\extraction_pc\\20210324142445.xml'
        file_sig = 'C:\\Users\\catec\\PycharmProjects\\MUOVI_pc\\..\\extraction_pc\\20210324142445.sig'
        sample_frequency, ad_bits = local_files_functions.read_xml(file_xml)
        comm, number_of_channels, sample_frequency, bytes_in_sample = local_files_functions.create_bin_command_xml(sample_frequency, ad_bits) # creo comando da lettura file locale

        self.handle_CB(comm)

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

        else:
            self.socket_M.close()
            print("STOP")


# MAIN
if __name__ == "__main__":
    MUOVI1 = MUOVI()
    # MUOVI1.main()
