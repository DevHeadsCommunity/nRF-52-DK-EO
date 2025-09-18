import pyvisa
import os


def test_scope_screenshot(visa_scope_sds804xhd_fixture, hil_results_get_path):

    try:
       # use the hil_results_get_path to get the path to the directory that will
       # be returned at the end of the test
        my_file_name = hil_results_get_path('screenshot.bmp')
        visa_scope_sds804xhd_fixture.take_screenshot(my_file_name)
       
    except Exception as err:
	    print('Exception: ' + str(err))
	    assert(False)