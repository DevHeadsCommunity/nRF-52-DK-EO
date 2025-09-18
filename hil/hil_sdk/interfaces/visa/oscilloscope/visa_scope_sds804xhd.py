import pyvisa
from hil_sdk.interfaces.visa.visa_equipment import VISAEquipment


class VISAScopeSDS804XHD(VISAEquipment):

    """
    Override the base class for the Siglent SDS804x HD oscilloscope
    """
    
    IDN_PATTERN = r'Siglent Technologies,SDS804X HD,SDS.*'
    
    def configure(self) -> None:
        self.instrument.write("AUT") #auto set the display

    def take_screenshot(self, filename: str) -> None:
        """
        Take a screenshot that outputs in BMP format
        """
        print(filename)
        f = open(filename, 'wb')

        # print the screen as a bmp file
        self.instrument.write("PRIN? BMP")
        
        result_str = self.instrument.read_raw()
        # get all chunks of data and send it into my file
        while (len(result_str) == self.instrument.chunk_size):
            f.write(result_str)
            f.flush()
            result_str = self.instrument.read_raw()

        # output the last chunk that's < chunk_size
        f.write(result_str)
        f.flush()
        f.close()