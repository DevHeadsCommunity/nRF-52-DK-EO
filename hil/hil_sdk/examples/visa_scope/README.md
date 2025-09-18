# VISA-compliant Oscilloscope Example Project

This example uses the Siglent SDS804X HD oscilloscope attached to the gateway to take a screenshot of the waveform during `test_scope_screenshot` test.

It consists of two files:

`conftest.py` - Implements a fixture that returns the `VISAScopeSDS804XHD()` interface in the `interfaces/visa/oscilloscopevisa_scope_sds804xhd.py` file

`test_screenshot.py` - Contains a test that takes a screenshot of the oscilloscope's display