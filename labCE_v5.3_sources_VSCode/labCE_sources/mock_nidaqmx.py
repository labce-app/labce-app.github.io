"""
Simulateur de carte d'acquisition NI USB-6341 - Compatible avec labCE
Émule le comportement de nidaqmx pour tester des applications sans matériel réel
Device: Dev1
Canaux: ai0 (Effort), ai1 (Course)
"""

import time
import random
import math

# ===================== CANAL SIMULÉ =====================
class SimulatedChannel:
    """Simule un canal analogique d'entrée avec signal réaliste"""
    def __init__(self, name, base_voltage=0.0, noise_level=0.01, signal_type='effort'):
        self.name = name
        self.base_voltage = base_voltage
        self.noise_level = noise_level
        self.signal_type = signal_type
        self.start_time = time.time()

    def read(self):
        """Génère une tension simulée réaliste pour essai mécanique"""
        elapsed = time.time() - self.start_time

        if self.signal_type == 'effort':
            if elapsed < 5:
                signal = (elapsed / 5.0) * 2.0  # Montée de 0 à 2V
            elif elapsed < 10:
                signal = 2.0 + math.sin(elapsed * 0.5) * 0.2  # Plateau avec oscillations
            elif elapsed < 15:
                signal = 2.0 - ((elapsed - 10) / 5.0) * 2.0  # Descente de 2V à 0V
            else:
                signal = math.sin(elapsed * 0.3) * 0.5  # Oscillations faibles
        else:  # 'course'
            if elapsed < 5:
                signal = (elapsed / 5.0) * 1.0  # Montée de 0 à 1V
            elif elapsed < 10:
                signal = 1.0 + math.sin(elapsed * 0.3) * 0.1  # Plateau avec oscillations
            elif elapsed < 15:
                signal = 1.0 - ((elapsed - 10) / 5.0) * 1.0  # Descente de 1V à 0V
            else:
                signal = math.sin(elapsed * 0.2) * 0.3  # Oscillations faibles

        noise = random.gauss(0, self.noise_level)
        return self.base_voltage + signal + noise

# ===================== CANAUX AI =====================
class SimulatedAIChannel:
    """Simule add_ai_voltage_chan de nidaqmx"""
    def __init__(self, physical_channel):
        self.physical_channel = physical_channel
        if 'ai0' in physical_channel:
            self.channel = SimulatedChannel(physical_channel, 0.5, 0.02, 'effort')
        elif 'ai1' in physical_channel:
            self.channel = SimulatedChannel(physical_channel, 0.2, 0.01, 'course')
        else:
            self.channel = SimulatedChannel(physical_channel, 0.0, 0.005, 'generic')

# ===================== TÂCHE DAQ =====================
class SimulatedAIChannels:
    """Simule task.ai_channels"""
    def __init__(self):
        self.channels = []

    def add_ai_voltage_chan(self, physical_channel, min_val=-10.0, max_val=10.0):
        """Ajoute un canal d'entrée analogique simulé"""
        channel = SimulatedAIChannel(physical_channel)
        self.channels.append(channel)
        return channel

class SimulatedTask:
    """Simule nidaqmx.Task - Compatible avec context manager"""
    def __init__(self):
        self.ai_channels = SimulatedAIChannels()
        self.is_started = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def start(self):
        self.is_started = True

    def stop(self):
        self.is_started = False

    def read(self, number_of_samples_per_channel=1):
        """Lit les valeurs simulées des canaux"""
        if not self.ai_channels.channels:
            raise Exception("Aucun canal configuré pour la lecture")

        values = [ch.channel.read() for ch in self.ai_channels.channels]
        return values

    def close(self):
        pass

# ===================== PÉRIPHÉRIQUE =====================
class SimulatedDevice:
    """Simule un périphérique NI USB-6341"""
    def __init__(self, name, product_type, serial_number):
        self.name = name
        self.product_type = product_type
        self.serial_number = serial_number
        self.is_present = True
        self.temperature = random.uniform(38.0, 43.0)

    def __repr__(self):
        return f"<Device {self.name} ({self.product_type})>"

# ===================== SYSTÈME =====================
class SimulatedSystem:
    """Simule nidaqmx.system.System"""
    def __init__(self):
        self.devices = [SimulatedDevice("Dev1", "USB-6341", "01E8A2B7")]

    @staticmethod
    def local():
        """Retourne le système local simulé"""
        return SimulatedSystem()

# ===================== EXCEPTIONS =====================
class DaqError(Exception):
    """Simule nidaqmx.DaqError"""
    pass

# ===================== MODULES EXPORTÉS =====================
system = SimulatedSystem
Task = SimulatedTask
DaqError = DaqError