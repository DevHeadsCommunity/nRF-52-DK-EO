import logging
from multiprocessing import Queue
from .ppk2_process import PPK2Process
import serial.tools.list_ports
from ..utility.child_worker import ChildWorkerCommand, ChildWorkerResponse

# Timeout to wait for any command to complete
# IMPORTANT: This must be longer than the longest expected command completion time,
#     which is currently "open" at around 3 seconds
COMMAND_TIMEOUT      = 5.0
PROCESS_JOIN_TIMEOUT = 5.0  # Seconds to wait for child process to cleanup and join (based on observed execution)

# Limits for VDD (based on documented HW limitations of PPK2, and Nordic's source)
VDD_MIN = 800
VDD_MAX = 5000

# Child process interface defines
STATUS_OK    = 0
STATUS_ERROR = -1

# Other constants
SAMPLE_SIZE_BYTES   = 4             # Each sample value is a 32-bit packed value
NUM_R_PARAMS        = 5             # Number of R params, equal to the number of measurement ranges
MAX_PAYLOAD_COUNTER = 0b111111      # 0x3f, 64 - 1: Counter overflow value
DATALOSS_THRESHOLD  = 500           # 500 * 10us = 5ms: allowed loss
ADC_MULT            = 1.8 / 163840  # Hardcoded value from Nordic source


class PPK2Interface:
    """
    Provides an interface to Nordic's PPK2 current measurement device. The sampling
    rate is fixed at 100 KS/s, which means that data collection has to be done in a
    separate process. This interface manages that child process, as well as converting the
    raw samples from the PPK2 into actual current values.
    """

    def __init__(self, serial_port: str = None) -> None:
        """
        Create the PPK2 interface.

        :param serial_port: Name of PPK2 serial port (or None to auto-detect)
        """
        self.serial_port_name = serial_port
        self.child_process = None
        self.samples = []
        self.current_vdd = 0
        self.metadata = None
        self.mode = None

    def open(self) -> bool:
        """
        Open PPK2 and launch a child process to collect data. This function
        also opens the serial port and resets the PPK2 prior to operation.

        :return: True on success, False otherwise.
        """
        try:
            if self.serial_port_name:
                self.port_name = self.serial_port_name
            else:
                device = PPK2Interface.find_ppk2_port()
                if device is None:
                    logging.error("No PPK2 device was found during auto-detection. Consider setting the port name explicitly.")
                    return False
                else:
                    self.port_name = device

            # Create and start the child process
            self.command_input_queue = Queue(maxsize=1)
            self.command_output_queue = Queue()
            self.child_process = PPK2Process(self.command_input_queue, self.command_output_queue)
            self.child_process.start()

            open_response = self._send_command("open", self.port_name)

            if open_response.status == STATUS_OK:
                metadata_bytes = open_response.data
                self.metadata = self._parse_metadata(metadata_bytes)

                if self.metadata is None:
                    return False
            else:
                logging.error("Error getting metadata from PPK2")
                return False

            return True

        except Exception as exc:
            logging.error(f"PPK2Interface.open error: {exc}")
            return False

    def close(self) -> bool:
        """
        Close the interface, stop the child process and cleanup all resources.

        :return: True on success, False otherwise.
        """
        try:
            # For safety, reset prior to closing
            self._send_command("close", None)

            if self.child_process is not None:
                # Wait five seconds for child to clean up gracefully before killing
                self.child_process.join(PROCESS_JOIN_TIMEOUT)

                if self.child_process.exitcode is None:
                    self.child_process.kill()  # Force kill child process
                    return False

            return True

        except Exception as exc:
            logging.error(f"PPK2Interface.close error: {exc}")
            return False

    def start_measuring(self) -> bool:
        """
        Start collecting current measurement data. The device must be open and a mode
        (either source or ampere meter) must be set prior to starting measuring.
        This function does not block, but instead starts collection on a background process.

        NOTE: After measuring is started, samples are collected at a rate of 100 KS/s (each sample is four bytes).
        It is the user's responsibility to ensure there is enough system memory to store the collected data.

        :return: True on success, False otherwise.
        """
        try:
            rsp = self._send_command("write", PPK2Commands.get_average_start_command())
            return rsp.status == STATUS_OK
        except Exception as exc:
            logging.error(f"PPK2Interface.start_measuring error: {exc}")
            return False

    def stop_measuring(self) -> bool:
        """
        Stop collecting current measurements and kill background thread.

        :return: True on success, False otherwise.
        """
        try:
            rsp = self._send_command("write", PPK2Commands.get_average_stop_command())

            if rsp.status != STATUS_OK:
                return False

            read_response = self._send_command("read_and_flush", None)

            if read_response.status == STATUS_OK:
                raw_samples = read_response.data
                self.samples = self._parse_raw_data(raw_samples)
            else:
                return False

            return True

        except Exception as exc:
            logging.error(f"PPK2Interface.stop_measuring error: {exc}")
            return False

    def set_source_meter_mode(self, vdd_mv: int) -> bool:
        """
        Set the PPK2 into source meter mode, where the PPK2 supplies power to the DUT.

        :param vdd_mv: VDD value, in millivolts.
        :return: True on success, False otherwise.
        """
        try:
            rsp1 = self._send_command("write", PPK2Commands.get_use_source_meter_command())
            rsp2 = self._send_command("write", PPK2Commands.get_set_vdd_command(vdd_mv))

            if rsp1.status != STATUS_OK or rsp2.status != STATUS_OK:
                return False

            self.current_vdd = vdd_mv
            return True

        except Exception as exc:
            logging.error(f"PPK2Interface.set_source_meter_mode error: {exc}")
            return False

    def set_ampere_meter_mode(self) -> bool:
        """
        Set the PPK2 into ampere meter mode, where the PPK2 is in series with the current to be measured.

        :return: True on success, False otherwise.
        """
        try:
            rsp = self._send_command("write", PPK2Commands.get_use_amp_meter_command())
            return rsp.status == STATUS_OK
        except Exception as exc:
            logging.error(f"PPK2Interface.set_ampere_meter_mode error: {exc}")
            return False

    def set_device_power(self, power_on: bool) -> bool:
        """
        Toggle the PPK2's power supply output.

        :param power_on: True if power supply should be enabled, False if it should be disabled.
        :return: True on success, False otherwise.
        """
        try:
            rsp = self._send_command("write", PPK2Commands.get_set_device_power_command(power_on))
            return rsp.status == STATUS_OK
        except Exception as exc:
            logging.error(f"PPK2Interface.set_device_power error: {exc}")
            return False

    def get_samples(self) -> list:
        """
        Return list of current measurement values. Units are amperes. The list may be empty
        if an error occurred during collection.

        :return: List of current measurement values.
        """
        return self.samples

    def _send_command(self, command_type: str, data) -> ChildWorkerResponse:
        """Send a command via the input queue and wait for a result from the output."""
        try:
            self.command_input_queue.put(ChildWorkerCommand(command_type, data))
            return self.command_output_queue.get(timeout=COMMAND_TIMEOUT)  # This is just a sensible timeout
        except:
            # Queue was empty
            return ChildWorkerResponse(STATUS_ERROR, None)

    def _parse_metadata(self, metadata_bytes):
        """Parse the raw metadata bytes into a map of coefficients and values."""
        try:
            if metadata_bytes is None:
                return None

            metadata_str = metadata_bytes.decode("utf-8").strip()
            metadata_split = metadata_str.split("\n")  # Each metadata item is separated by a newline

            if metadata_split[-1] != "END":
                # Full metadata not received, or corrupted
                return None

            metadata_map = {}
            for item in metadata_split[:-1]:
                # Each metadata coefficient pair is in the format NAME:VALUE
                name = item.split(":")[0].strip()
                val  = item.split(":")[1].strip()
                metadata_map[name] = float(val)

            return metadata_map

        except Exception as e:
            print(f"Error parsing metadata: {str(e)}")
            return None

    @staticmethod
    def find_ppk2_port():
        """Search existing COM ports for the PPK2 device."""
        com_ports = serial.tools.list_ports.comports()
        for port in com_ports:
            if port.product == "PPK2":
                return port.device  # Returns the first device
        return None

    def _parse_raw_data(self, raw_samples) -> list:
        """Parse our raw sample buffer."""
        num_samples = len(raw_samples) // SAMPLE_SIZE_BYTES
        samples = []

        for i in range(num_samples):
            start_index = i * SAMPLE_SIZE_BYTES
            data = raw_samples[start_index:start_index + SAMPLE_SIZE_BYTES]
            adc_value = self._parse_raw_measurement(data)

            if adc_value is not None:
                samples.append(adc_value)

        return samples

    def _parse_raw_measurement(self, data_bytes):
        """Parse four raw bytes into a current measurement."""
        if len(data_bytes) != SAMPLE_SIZE_BYTES:
            return None

        raw_value = int.from_bytes(data_bytes, byteorder="little", signed=False)

        # Masks and shifts for the four packed values
        ADC_MASK      = 0b00000000000000000011111111111111
        ADC_SHIFT     = 0
        RANGE_MASK    = 0b00000000000000011100000000000000
        RANGE_SHIFT   = 14
        COUNTER_MASK  = 0b00000000111111000000000000000000
        COUNTER_SHIFT = 18
        LOGIC_MASK    = 0b11111111000000000000000000000000
        LOGIC_SHIFT   = 24

        range_value   = (raw_value & RANGE_MASK) >> RANGE_SHIFT
        counter       = (raw_value & COUNTER_MASK) >> COUNTER_SHIFT
        adc_value     = (raw_value & ADC_MASK)     >> ADC_SHIFT
        bits          = (raw_value & LOGIC_MASK)   >> LOGIC_SHIFT

        adc_value *= 4  # Taken from Nordic Desktop code, unsure of reason
        current_range = min(range_value, NUM_R_PARAMS)

        adc = self._get_adc_result(adc_value, current_range)

        return adc

    def _get_adc_result(self, adc_value, range):
        """Given a raw ADC value, use the metadata coefficients to calculate current measurement."""
        if self.metadata is None:
            return None

        # Read coefficient values from metadata
        r_coeff  = self.metadata.get("R%d"  % range)
        gs_coeff = self.metadata.get("GS%d" % range)
        gi_coeff = self.metadata.get("GI%d" % range)
        o_coeff  = self.metadata.get("O%d"  % range)
        s_coeff  = self.metadata.get("S%d"  % range)
        i_coeff  = self.metadata.get("I%d"  % range)
        ug_coeff = self.metadata.get("UG%d" % range)

        result_without_gain = (adc_value - o_coeff) * (ADC_MULT / r_coeff)

        adc = ug_coeff * (result_without_gain * (gs_coeff * result_without_gain + gi_coeff) + (s_coeff * (self.current_vdd / 1000) + i_coeff))

        return adc


class PPK2Commands:
    NO_OP = 0x00
    TRIGGER_SET = 0x01
    AVG_NUM_SET = 0x02
    TRIGGER_WINDOW_SET = 0x03
    TRIGGER_INTERVAL_SET = 0x04
    TRIGGER_SINGLE_SET = 0x05
    AVERAGE_START = 0x06
    AVERAGE_STOP = 0x07
    RANGE_SET = 0x08
    LCD_SET = 0x09
    TRIGGER_STOP = 0x0a
    DEVICE_RUNNING_SET = 0x0c
    REGULATOR_SET = 0x0d
    SWITCH_POINT_DOWN = 0x0e
    SWITCH_POINT_UP = 0x0f
    TRIGGER_EXT_TOGGLE = 0x11
    SET_POWER_MODE = 0x11
    RES_USER_SET = 0x12
    SPIKE_FILTERING_ON = 0x15
    SPIKE_FILTERING_OFF = 0x16
    GET_METADATA = 0x19
    RESET = 0x20
    SET_USER_GAINS = 0x25

    @staticmethod
    def get_set_vdd_command(mv: int) -> bytearray:
        # Clamp mv value within range
        mv = min(VDD_MAX, max(VDD_MIN, mv))
        return bytearray([PPK2Commands.REGULATOR_SET, mv >> 8, mv & 0xff])

    @staticmethod
    def get_set_device_power_command(power_on: bool):
        if power_on:
            return bytearray([PPK2Commands.DEVICE_RUNNING_SET, PPK2Commands.TRIGGER_SET])
        else:
            return bytearray([PPK2Commands.DEVICE_RUNNING_SET, PPK2Commands.NO_OP])

    @staticmethod
    def get_average_start_command():
        return bytearray([PPK2Commands.AVERAGE_START])

    @staticmethod
    def get_average_stop_command():
        return bytearray([PPK2Commands.AVERAGE_STOP])

    @staticmethod
    def get_device_running_command(running: bool):
        return bytearray([PPK2Commands.DEVICE_RUNNING_SET, PPK2Commands.TRIGGER_SET if running else PPK2Commands.NO_OP])

    @staticmethod
    def get_use_source_meter_command():
        return bytearray([PPK2Commands.SET_POWER_MODE, PPK2Commands.AVG_NUM_SET])

    @staticmethod
    def get_use_amp_meter_command():
        return bytearray([PPK2Commands.SET_POWER_MODE, PPK2Commands.TRIGGER_SET])

    @staticmethod
    def get_get_metadata_command():
        return bytearray([PPK2Commands.GET_METADATA])

    @staticmethod
    def get_reset_command():
        return bytearray([PPK2Commands.RESET])
