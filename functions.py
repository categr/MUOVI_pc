# -*- coding: utf-8 -*-
import numpy as np


# conversione in rappresentazione binaria di 1 byte
def byte_to_binary(byte):
    byte = int.from_bytes(byte, byteorder="big")

    # Usa la funzione bin() per ottenere la rappresentazione binaria e rimuovi il prefisso '0b'
    binary_representation = bin(byte)[2:]

    # Aggiungi zeri iniziali se la lunghezza della stringa binaria è inferiore a 8
    binary_representation = '0' * (8 - len(binary_representation)) + binary_representation

    return binary_representation


# Convert integer to bytes (COMMAND INTEGERS)
def integer_to_bytes(command):
    return int(command).to_bytes(1,
                                 byteorder="big")  # byte più significativo a sx, ma in questo caso l'intero command viene convertito e memorizzato su un solo byte


# presa e modificata da communication.py
# Create the binary command which is sent to Muovi
# to start or stop the communication with wanted data logging setup
def create_bin_command(start=1):
    # Refer to the communication protocol for details about these variables:
    ProbeEN = 1  # 1 = Probe enabled, 0 = probe disabled (bit0)
    EMG = 1  # 1 = EMG, 0 = EEG (bit 3)
    Mode0 = 1  # [00 01 10 11] = [monop monop16 impCk Test]
    Mode1 = 1
    # Mode = 0       # 0 = 32Ch Monop, 1 = 16Ch Monop, 2 = 32Ch ImpCk, 3 = 32Ch Test (bit 1 e 2)
    # control byte: 0 0 0 0 EMG Mode_bit2 Mode_bit1 ProbeEN

    # Number of acquired channel depending on the acquisition mode
    # NumChanVsMode = np.array([38,22,38,38])

    number_of_channels = None
    sample_frequency = None
    bytes_in_sample = None

    # Create the command to send to Muovi
    command = 0
    if ProbeEN == 1:
        command = 0 + EMG * 8 + + Mode1 * 4 + Mode0 * 2 + 1  # conv in decimale (ProbeEN=1*2^0+ Mode*2^1)
        if Mode0 == 0 and Mode1 == 1:
            # number_of_channels = NumChanVsMode[Mode]
            number_of_channels = 22
        else:
            number_of_channels = 38

        if EMG == 0:
            sample_frequency = 500;  # Sampling frequency = 500 for EEG
        else:
            sample_frequency = 2000;  # Sampling frequency = 2000 for EMG

    if EMG == 1:
        bytes_in_sample = 2
    else:
        bytes_in_sample = 3

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


# converte un valore compreso tra 0 e il massimo numero rappresentabile su 3 byte in un numero rappresentato su 3 byte
def pack_uint24(value):
    # Assicurati che il valore sia compreso nel range da 0 a 16777215 (2^24 - 1)
    if not 0 <= value <= 16777215:
        raise ValueError("Il valore deve essere compreso tra 0 e 16777215 (inclusi)")

    # Converti il numero in 3 byte utilizzando il byte più significativo (MSB) per primo (formato big-endian)
    return bytes([(value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF])
# shift a destra di 16 bit del numero e operazione and con 11111111, shit a destra di 8 bit e and, tutto il numero così e and
