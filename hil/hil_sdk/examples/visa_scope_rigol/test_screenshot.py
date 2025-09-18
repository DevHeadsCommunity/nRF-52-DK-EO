import pyvisa
import os


def test_scope_screenshot(visa_scope_ds1104z_fixture, hil_results_get_path):

    try:
       # use the hil_results_get_path to get the path to the directory that will
       # be returned at the end of the test
        my_file_name = hil_results_get_path('screenshot.png')
        visa_scope_ds1104z_fixture.take_screenshot(my_file_name)
       
    except Exception as err:
	    print('Exception: ' + str(err))
	    assert(False)