# VISA-compliant Oscilloscope Example Project

This example uses the Rigol DS1104Z oscilloscope attached to the gateway to take a screenshot of the waveform during `test_scope_screenshot` test.

It consists of two files:

`conftest.py` - Implements a fixture that returns the `VISAScopeDS1104Z()` interface

`test_screenshot.py` - Contains a test that takes a screenshot of the oscilloscope's display