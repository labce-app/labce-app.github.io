"""
Module d'acquisition NI-DAQmx Hybride (Analogique + Encodeur Linéaire)
labCE v5.2 - USB-6341 | Kistler 9217A (ai0) + Encodeur linéaire ASM PMIS3 (ctr0)

Architecture calquée sur LabVIEW NI :
  - Tâche AI (maître) : effort sur ai0, RSE ±10V, sample clock interne
  - Tâche CI (esclave) : encodeur linéaire sur ctr0, cadencé sur ai/SampleClock
  - add_ci_lin_encoder_chan (pas add_ci_ang_encoder_chan — l'ASM PMIS3 est linéaire)
  - dist_per_pulse = sensibilité course (mm/pas) convertie en mètres
  - Le driver NI retourne directement la position en mètres → conversion m→mm
  - PFI A/B assignés explicitement (PFI9/PFI8 par défaut, inversable)
"""
import logging
import time
import threading
import numpy as np
from config import AcquisitionConfig, ENCODER_CONFIG

try:
    import nidaqmx
    import nidaqmx.system as system
    from nidaqmx.constants import AcquisitionType, TerminalConfiguration
    HAS_NIDAQMX = True

    # === Résolution robuste des constantes encodeur LINÉAIRE ===
    # nidaqmx 1.4.0 : EncoderType.X_4, LengthUnits.METERS
    _ENCODER_X4 = None
    _LENGTH_METERS = None

    try:
        from nidaqmx.constants import EncoderType, LengthUnits

        # EncoderType.X_4 (nidaqmx 1.4.0+)
        for attr in ('X_4', 'X4', 'x4', 'X_4_ENCODING', 'FOUR_X'):
            val = getattr(EncoderType, attr, None)
            if val is not None:
                _ENCODER_X4 = val
                break
        if _ENCODER_X4 is None:
            for member in EncoderType:
                if '4' in str(member.name) or member.value == 10195:
                    _ENCODER_X4 = member
                    break
        if _ENCODER_X4 is None:
            try:
                _ENCODER_X4 = EncoderType(10195)
            except Exception:
                pass

        # LengthUnits.METERS
        for attr in ('METERS', 'meters', 'Meters', 'METER'):
            val = getattr(LengthUnits, attr, None)
            if val is not None:
                _LENGTH_METERS = val
                break
        if _LENGTH_METERS is None:
            for member in LengthUnits:
                if 'meter' in str(member.name).lower() or member.value == 10219:
                    _LENGTH_METERS = member
                    break
        if _LENGTH_METERS is None:
            try:
                _LENGTH_METERS = LengthUnits(10219)
            except Exception:
                pass

        logging.info(
            f"Encodeur linéaire config: X4={_ENCODER_X4}, "
            f"METERS={_LENGTH_METERS}")
        if _ENCODER_X4 is None or _LENGTH_METERS is None:
            logging.error(
                "Impossible de résoudre les constantes encodeur linéaire! "
                f"EncoderType members: {[m.name for m in EncoderType]}, "
                f"LengthUnits members: {[m.name for m in LengthUnits]}")

    except ImportError:
        logging.warning(
            "EncoderType/LengthUnits non trouvés - encodeur désactivé")

except ImportError:
    HAS_NIDAQMX = False
    _ENCODER_X4 = None
    _LENGTH_METERS = None
    logging.warning("Module nidaqmx manquant - Simulation")


class NIDeviceManager:
    @staticmethod
    def is_available():
        return HAS_NIDAQMX

    @staticmethod
    def detect_devices():
        if not HAS_NIDAQMX:
            return None
        try:
            return list(system.System.local().devices)
        except Exception:
            return None

    @staticmethod
    def test_connection(device_name, effort_channel, course_channel):
        """Test la connexion au device NI. Ne teste que le canal AI effort."""
        if not HAS_NIDAQMX:
            return False
        try:
            with nidaqmx.Task() as t:
                t.ai_channels.add_ai_voltage_chan(
                    f"{device_name}/{effort_channel}",
                    terminal_config=TerminalConfiguration.RSE)
                t.start()
                t.read()
            return True
        except Exception as e:
            logging.error(f"Erreur test connexion: {e}")
            return False

    @staticmethod
    def perform_tare(device_name, effort_channel, course_channel,
                     num_samples=100):
        """
        Tare effort (analogique) et course (analogique uniquement).
        Pour l'encodeur, la tare est logicielle (position = 0 au démarrage,
        gérée par initial_pos=0.0 dans add_ci_lin_encoder_chan).
        """
        if not HAS_NIDAQMX:
            return None
        try:
            offset_effort = 0.0
            offset_course = 0.0

            # Tare effort (toujours analogique)
            with nidaqmx.Task() as task:
                task.ai_channels.add_ai_voltage_chan(
                    f"{device_name}/{effort_channel}",
                    terminal_config=TerminalConfiguration.RSE)
                task.start()
                data = task.read(number_of_samples_per_channel=num_samples)
                offset_effort = float(np.mean(data))

            # Tare course uniquement si analogique (ai*)
            if "ai" in course_channel.lower():
                with nidaqmx.Task() as task:
                    task.ai_channels.add_ai_voltage_chan(
                        f"{device_name}/{course_channel}",
                        terminal_config=TerminalConfiguration.RSE)
                    task.start()
                    data = task.read(
                        number_of_samples_per_channel=num_samples)
                    offset_course = float(np.mean(data))
            # Si encodeur (ctr*), pas de tare analogique — initial_pos=0.0

            return (offset_effort, offset_course)
        except Exception as e:
            logging.error(f"Erreur tare: {e}")
            return None


class AcquisitionThread:
    """
    Thread d'acquisition hybride : AI (effort) + CI encodeur linéaire ou AI (course).

    Mode encodeur (ctr0) :
      - Tâche AI (maître) : ai0, sample clock interne
      - Tâche CI (esclave) : ctr0 avec add_ci_lin_encoder_chan
        → dist_per_pulse = sens_course converti en mètres
        → Le driver NI retourne directement la position en mètres
        → On convertit mètres → mm dans la boucle
      - CI cadencé sur /{device}/ai/SampleClock (esclave démarré avant maître)

    Mode analogique (ai1) :
      - Tâche AI unique : ai0 (effort) + ai1 (course) sur même clock
    """

    def __init__(self, device_name, effort_channel, course_channel,
                 frequency, sens_effort, sens_course,
                 offset_effort, offset_course, data_manager,
                 update_callback=None, error_callback=None,
                 pfi_a="PFI9", pfi_b="PFI8",
                 initial_pos_m=0.0, time_offset=0.0):
        self.device_name = device_name
        self.effort_channel = effort_channel    # ex: ai0
        self.course_channel = course_channel    # ex: ctr0 ou ai1
        self.frequency = int(frequency)
        self.sens_effort = float(sens_effort)   # N/V
        self.sens_course = float(sens_course)   # mm/pas (encodeur) ou mm/V (analog)
        self.offset_effort = float(offset_effort)
        self.offset_course = float(offset_course)
        self.data_manager = data_manager
        self.update_callback = update_callback
        self.error_callback = error_callback
        self.pfi_a = pfi_a
        self.pfi_b = pfi_b
        self.initial_pos_m = float(initial_pos_m)  # Position de départ encodeur (m)
        self.time_offset = float(time_offset)       # Décalage temporel pour continuité
        self._running = False
        self._thread = None

        # Détection auto du mode encodeur
        self.is_encoder = "ctr" in self.course_channel.lower()

    def start(self):
        if self._running:
            return False
        self._running = True
        self._thread = threading.Thread(
            target=self._acquisition_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        self.data_manager.stop_csv_writer()

    def is_running(self):
        return self._running

    def _acquisition_loop(self):
        sample_counter = 0
        last_update = time.time()
        task_ai = None
        task_ci = None

        try:
            # === TÂCHE ANALOGIQUE (MAÎTRE) - effort sur ai0 ===
            task_ai = nidaqmx.Task("labCE_AI")
            task_ai.ai_channels.add_ai_voltage_chan(
                f"{self.device_name}/{self.effort_channel}",
                terminal_config=TerminalConfiguration.RSE,
                min_val=-10.0, max_val=10.0)

            if self.is_encoder:
                # ========================================================
                # MODE ENCODEUR LINÉAIRE (architecture LabVIEW NI)
                # ========================================================
                # Vérifier constantes
                if _ENCODER_X4 is None or _LENGTH_METERS is None:
                    members_enc = "N/A"
                    members_len = "N/A"
                    try:
                        members_enc = [m.name for m in EncoderType]
                    except Exception:
                        pass
                    try:
                        members_len = [m.name for m in LengthUnits]
                    except Exception:
                        pass
                    raise RuntimeError(
                        f"Constantes encodeur linéaire non disponibles "
                        f"(nidaqmx v{nidaqmx.__version__}).\n"
                        f"EncoderType X4={_ENCODER_X4}, "
                        f"LengthUnits METERS={_LENGTH_METERS}\n"
                        f"EncoderType members: {members_enc}\n"
                        f"LengthUnits members: {members_len}")

                # dist_per_pulse : convertir mm/pas → mètres/pas
                # sens_course est en mm/pas (ex: 0.004 mm/pas)
                # NI attend des mètres/pulse : 0.004 mm = 0.000004 m
                dist_per_pulse_m = self.sens_course / 1000.0

                task_ci = nidaqmx.Task("labCE_CI_Encoder")

                # --- CANAL ENCODEUR LINÉAIRE ---
                # add_ci_lin_encoder_chan : la bonne fonction pour ASM PMIS3
                # (et non add_ci_ang_encoder_chan qui est pour rotatif)
                # Le driver NI fait la conversion pulse → mètres tout seul
                chan = task_ci.ci_channels.add_ci_lin_encoder_chan(
                    counter=f"{self.device_name}/{self.course_channel}",
                    decoding_type=_ENCODER_X4,
                    zidx_enable=False,
                    units=_LENGTH_METERS,
                    dist_per_pulse=dist_per_pulse_m,
                    initial_pos=self.initial_pos_m)

                # --- BORNES PFI EXPLICITES ---
                chan.ci_encoder_a_input_term = (
                    f"/{self.device_name}/{self.pfi_a}")
                chan.ci_encoder_b_input_term = (
                    f"/{self.device_name}/{self.pfi_b}")

                # --- FILTRE NUMÉRIQUE HARDWARE (architecture LabVIEW NI-DAQmx) ---
                # Filtre les impulsions parasites sur PFI A/B : rebonds mécaniques,
                # couplage EMI lors des décélérations/arrêts du banc.
                # Largeur minimale = 5 µs : compatible 50 kHz max ASM PMIS3
                # (période min d'un front X4 à 50 kHz = 1/(50000*4) = 5 µs).
                # Tout pulse plus court est ignoré par le compteur NI → plus de
                # dérive de position après arrêt du banc.
                _DIG_FILTER_WIDTH_S = 5e-6  # 5 µs
                try:
                    chan.ci_encoder_a_input_dig_fltr_enable = True
                    chan.ci_encoder_b_input_dig_fltr_enable = True
                    chan.ci_encoder_a_input_dig_fltr_min_pulse_width = _DIG_FILTER_WIDTH_S
                    chan.ci_encoder_b_input_dig_fltr_min_pulse_width = _DIG_FILTER_WIDTH_S
                    logging.info(
                        f"Filtre numérique PFI activé : "
                        f"{_DIG_FILTER_WIDTH_S * 1e6:.0f} µs min "
                        f"sur A={self.pfi_a} / B={self.pfi_b}")
                except Exception as e_fltr:
                    logging.warning(
                        f"Filtre numérique PFI non disponible sur cette carte "
                        f"(propriété non supportée) : {e_fltr}")

                logging.info(
                    f"Encodeur linéaire configuré: "
                    f"{ENCODER_CONFIG['name']}, "
                    f"X4, A={self.pfi_a}/B={self.pfi_b}, "
                    f"dist_per_pulse={dist_per_pulse_m:.6f} m "
                    f"({self.sens_course} mm/pas)")

                # === TIMING : AI maître, CI esclave ===
                task_ai.timing.cfg_samp_clk_timing(
                    rate=self.frequency,
                    sample_mode=AcquisitionType.CONTINUOUS,
                    samps_per_chan=self.frequency * 10)

                # CI esclave cadencé sur le sample clock de AI
                clk_src = f"/{self.device_name}/ai/SampleClock"
                task_ci.timing.cfg_samp_clk_timing(
                    rate=self.frequency,
                    source=clk_src,
                    sample_mode=AcquisitionType.CONTINUOUS,
                    samps_per_chan=self.frequency * 10)

            else:
                # ========================================================
                # MODE ANALOGIQUE PUR (ai0 effort + ai1 course)
                # ========================================================
                task_ai.ai_channels.add_ai_voltage_chan(
                    f"{self.device_name}/{self.course_channel}",
                    terminal_config=TerminalConfiguration.RSE,
                    min_val=-10.0, max_val=10.0)

                task_ai.timing.cfg_samp_clk_timing(
                    rate=self.frequency,
                    sample_mode=AcquisitionType.CONTINUOUS,
                    samps_per_chan=self.frequency * 10)

            # === DÉMARRAGE : esclave AVANT maître (règle LabVIEW) ===
            if task_ci:
                task_ci.start()
            task_ai.start()

            mode_str = (
                f"Encodeur linéaire (ctr0: A={self.pfi_a}/B={self.pfi_b}, "
                f"{self.sens_course} mm/pas)"
                if self.is_encoder else "Analogique pur")
            logging.info(
                f"Acquisition démarrée - {mode_str} @ {self.frequency} Hz")

            # Nombre d'échantillons par lecture (~5 mises à jour/s)
            samples_to_read = max(1, int(self.frequency / 5))

            while self._running:
                # --- Lecture AI (effort en volts) ---
                data_ai = task_ai.read(
                    number_of_samples_per_channel=samples_to_read)

                if self.is_encoder:
                    # --- Lecture CI (position en MÈTRES, grâce au driver) ---
                    data_ci = task_ci.read(
                        number_of_samples_per_channel=samples_to_read)

                    # data_ai = [v1, v2, ...] (1 canal AI = tension effort)
                    # data_ci = [pos1_m, pos2_m, ...] (position en mètres)
                    raw_effort_list = data_ai

                    # Conversion mètres → millimètres
                    raw_course_mm = [pos_m * 1000.0 for pos_m in data_ci]
                else:
                    # data_ai = [[effort_v...], [course_v...]] (2 canaux)
                    raw_effort_list = data_ai[0]
                    raw_course_v_list = data_ai[1]

                for i in range(len(raw_effort_list)):
                    # Temps continu depuis le début de la session complète
                    current_time = self.time_offset + sample_counter / self.frequency

                    v_effort = raw_effort_list[i]

                    if self.is_encoder:
                        # Course déjà en mm (driver a fait la conversion)
                        course = raw_course_mm[i]
                        v_course = 0.0
                    else:
                        # Course analogique : tension → mm
                        v_course = raw_course_v_list[i]
                        course = ((v_course - self.offset_course)
                                  * self.sens_course)

                    # Effort : tension → Newtons (offset statique de tare uniquement)
                    # La correction de dérive dynamique a été supprimée car elle
                    # causait des chutes à 0N lors des arrêts du banc.
                    effort = (v_effort - self.offset_effort) * self.sens_effort

                    self.data_manager.add_sample(
                        current_time, effort, course, v_effort, v_course)
                    sample_counter += 1

                # Callback mise à jour graphique
                now = time.time()
                if now - last_update > AcquisitionConfig.PLOT_UPDATE_INTERVAL:
                    if self.update_callback:
                        self.update_callback(
                            self.data_manager.get_latest_values())
                    last_update = now

        except Exception as e:
            self._running = False
            if self.error_callback:
                self.error_callback(str(e))
            logging.error(f"Erreur acquisition: {e}", exc_info=True)

        finally:
            # Fermeture propre : stop puis close (comme LabVIEW Clear Task)
            for task_name, task_obj in [("CI", task_ci), ("AI", task_ai)]:
                if task_obj:
                    try:
                        task_obj.stop()
                    except Exception:
                        pass
                    try:
                        task_obj.close()
                    except Exception:
                        pass
            logging.info("Tâches d'acquisition fermées proprement")