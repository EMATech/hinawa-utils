#!/usr/bin/env python3

from gi.repository import Hinawa

from ta1394.general import AvcGeneral
from ta1394.ccm import AvcCcm

path = '/dev/fw{0}'.format(argv[1])
unit = Hinawa.FwUnit(path)
unit.listen()

fcp = Hinawa.FwFcp()
fcp.listen(unit)

clk_dst = AvcCcm.get_subunit_signal_addr('music', 0, 17)
# Sync to cycle start packet in IEEE 1394 bus, generally OHCI 1394
# host controller generates the packet, thus in fact the device
# synchronizes to  cycle of the controller.
clk_csp_src = AvcCcm.get_subunit_signal_addr('music', 0, 17)
# Word clock input.
clk_word_src = AvcCcm.get_unit_signal_addr('external', 17)
# Some digital signals to optical interface.
clk_opt_src = AvcCcm.get_unit_signal_addr('external', 18)

# Retrieve current source
curr_src = AvcCcm.get_signal_source(fcp, clk_dst)
# The curr_src may be one of the above sources.

# Check avail or not
# If not, exception raises.
AvcCcm.ask_signal_source(fcp, clk_csp_src)
AvcCcm.ask_signal_source(fcp, clk_word_src)
AvcCcm.ask_signal_source(fcp, clk_opt_src)

# Change signal source
# I mis-spelled the name of function...
AvcCcm.set_signal_souarce(fcp, clk_dst)
AvcCcm.set_signal_souarce(fcp, clk_word_src)
AvcCcm.set_signal_souarce(fcp, clk_opt_src)

