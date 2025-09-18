
import pyvisa
import re

class VISAInterfaceException(Exception):
    pass

class VISAEquipment:

    """Base class that represents an instance of a VISA-compliant device"""

    # Pattern to match the result of a '*IDN?' query
    IDN_PATTERN = r''

    def __init__(self) -> None:

        """
        Create an instance of a VISA-compliant device using a given IDN_PATTERN
        to find the related instrument connected to the gateway.
        If found, it will then configure it for before the test runs
        """

        try:
            self.resource_manager = pyvisa.ResourceManager('@py')
            if self.find_device():
                self.configure()
            else:
                raise VISAInterfaceException(f"Cannot find connected device with a response to the IDN query that matches the pattern of '{self.IDN_PATTERN}'")
        except Exception as exc:
            raise VISAInterfaceException(f"Device setup and configuration failed") from exc


    def find_device(self) -> bool:

        """
        Find all resources attached to the gateway and select the first one that matches the IDN_PATTERN
        NOTE: this will select the first found device that matches, multiple of the same device is not supported
        """

        #loop through the given resources
        for resource_name in self.resource_manager.list_resources():
            #attempt to open and do an IDN query
            try:
                inst = self.resource_manager.open_resource(resource_name)
                idn_string = inst.query('*IDN?')
                if re.search(self.IDN_PATTERN, idn_string):
                    #if this instrument matches the IDN pattern, use this and return
                    #TODO may want to update this to handle multiple of the same device on a GW?
                    self.instrument = inst
                    return True;
                inst.close()
            except Exception as exc:
                pass # if an open fails, just try to keep going
        return False;

        
    def configure(self) -> None:

        """
        Override this function to configure your particular device. 
        Used during initializing the class to get the device into a known state
        """
        pass

    def take_screenshot(self, filename: str) -> None:
        """
        Override this function to take a screenshot of the display of your particular device
        :param filename: Path of the file the screenshot will be saved at
        """
        pass

    def write(self, SCPI: str) -> None:
        """
        Write a SCPI command to the device
        :param SCPI: must be a valid SCPI command for the given device
        """
        self.instrument.write(SCPI)
    
    def query(self, SCPI: str) -> str:
        """
        Write a SCPI command to the device and then read the result
        :param SCPI: must be a valid SCPI command for the given device
        """
        return self.instrument.query(SCPI)
    
    def read(self) -> str:
        """
        Read the device
        """
        return self.instrument.read()