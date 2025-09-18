#
# Copyright (C) 2024, Dojo Five
# All rights reserved.
#
import time
import statistics

POWER_SUPPLY_MV = 5000  # 5V USB power supply

def test_ppk(ppk2_fixture):

    assert ppk2_fixture.start_measuring()
    time.sleep(5)
    ppk2_fixture.stop_measuring()

    # Measurements are originally in amps
    avg_current_mA = statistics.mean(ppk2_fixture.get_samples()) * 1000

    print(f"Average current: {avg_current_mA} mA")
    print(f"Average power consumption: {avg_current_mA * POWER_SUPPLY_MV} mW")
