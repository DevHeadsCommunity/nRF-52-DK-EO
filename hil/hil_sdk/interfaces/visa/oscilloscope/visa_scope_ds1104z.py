import pyvisa
from hil_sdk.interfaces.visa.visa_equipment import VISAEquipment


class VISAScopeDS1104Z(VISAEquipment):

    """
    Override the base class for the Rigol DS1104Z oscilloscope
    """
    
    IDN_PATTERN = r'RIGOL TECHNOLOGIES,DS1104Z,DS.*'
    
    def configure(self) -> None:
        self.instrument.write("AUT") #auto set the display
        self.instrument.chunk_size = 52 #very small chunk sizes are needed for rigol scopes
        self.instrument.timeout = 10000 # set a timeout of 10 seconds to prevent hanging forever

    def take_screenshot(self, filename: str) -> None:
        """
        Take a screenshot that outputs in png format
        """
        print(filename)
        f = open(filename, 'wb')

        # print the screen as a bmp file
        result_str = self.instrument.query_binary_values(':DISP:DATA? ON,0,PNG', datatype='B')
        
        f.write(bytearray(result_str))
        f.flush()
        f.close()