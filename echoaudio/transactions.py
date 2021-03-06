from array import array
from math import log10
from gi.repository import Hinawa

# This should not be imported.
def get_array():
    # The width with 'L' parameter is depending on environment.
    arr = array('L')
    if arr.itemsize is not 4:
        arr = array('I')
        if arr.itemsize is not 4:
            raise RuntimeError('Platform has no representation \
                                equivalent to quadlet.')
    return arr

# This should not be imported.
def calculate_vol_from_db(db):
    if db <= -144.0:
        return 0x00000000
    else:
        return int(0x01000000 * pow(10, db / 20))

# This should not be imported.
def calculate_vol_to_db(vol):
    if vol == 0:
        return -144.0
    else:
        return 20 * log10(vol / 0x01000000)

#
# Category No.0, for hardware information
#
class EftInfo():
    supported_features = (
        'changeable-resp-addr',
        'aesebu-xlr',
        'control-room-mirroring',
        'spdif-coax',
        'dsp',
        'fpga',
        'phantom-powering',
        'rx-mapping',
        'adjust-input-level',
        'spdif-opt',
        'adat-opt',
        'nominal-input',
        'nominal-output',
        'soft-clip',
        'robot-hex-input',
        'robot-battery-charge',
        # For our purpose
        'tx-mapping',
    )

    supported_clock_sources = (
        'internal',
        'syt-match',
        'word-clock',
        'spdif',
        'ADAT-1',
        'ADAT-2',
        'continuous'
    )

    supported_sampling_rates = (
        32000, 44100, 48000,
        88200, 96000,
        176400, 192000
    )

    supported_firmwares = ('ARM', 'DSP', 'FPGA')

    supported_port_names = (
        'analog',
        'spdif',
        'adat',
        'spdif/adat',
        'analog mirroring',
        'headphones',
        'I2S',
        'guitar',
        'piezo guitar',
        'guitar string'
    )

    _feature_flags = {
        'changeable-resp-addr':    0x0001,
        'aesebu-xlr':              0x0002,
        'control-room-mirroring':  0x0004,
        'spdif-coax':              0x0008,
        'dsp':                     0x0010,
        'fpga':                    0x0020,
        'phantom-powering':        0x0040,
        'rx-mapping':              0x0080,
        'adjust-input-level':      0x0100,
        'spdif-opt':               0x0200,
        'adat-opt':                0x0400,
        'nominal-input':           0x0800,
        'nominal-output':          0x1000,
        'soft-clip':               0x2000,
        'robot-hex-input':         0x4000,
        'robot-battery-charge':    0x8000,
    }

    _clock_flags = {
        'internal':    0x0001,
        'syt-match':   0x0002,
        'word-clock':  0x0004,
        'spdif':       0x0008,
        'adat1':       0x0010,
        'adat2':       0x0020,
        'continuous':  0x0040,
    }

    _midi_flags = {
        'midi-in-1':        0x00000100,
        'midi-out-1':       0x00000200,
        'midi-in-2':        0x00000400,
        'midi-out-2':       0x00000800,
    }

    _robot_flags = {
        'battery-charging': 0x20000000,
        'stereo-connect':   0x40000000,
        'hex-signal':       0x80000000,
    }

    def _execute_command(unit, cmd, args):
        if not isinstance(unit, Hinawa.SndEfw):
            raise ValueError('Invalid argument for SndEfw')
        return unit.transact(0, cmd, args)

    @staticmethod
    def get_spec(unit):
        args = get_array()
        params = EftInfo._execute_command(unit, 0, args)
        info = {}
        info['features'] = EftInfo._parse_capability(params)
        info['clock-sources'] = EftInfo._parse_clock_source(params)
        info['sampling-rates'] = EftInfo._parse_sampling_rate(params)
        info.update(EftInfo._parse_phys_ports(params))
        info.update(EftInfo._parse_mixer_channels(params))
        info.update(EftInfo._parse_stream_formation(params))
        info['firmware-versions'] = EftInfo._parse_firmware_versions(params)
        return info

    @staticmethod
    def get_metering(unit):
        args = get_array()
        params = EftInfo._execute_command(unit, 1, args)
        metering = {}
        metering['clocks'] = {}
        for name, flag in EftInfo._clock_flags.items():
            if params[0] & flag:
                metering['clocks'][name] = True
            else:
                metering['clocks'][name] = False
        metering['midi'] = {}
        for name, flags in EftInfo._midi_flags.items():
            if params[0] & flag:
                metering['midi'][name] = True
            else:
                metering['midi'][name] = False
        metering['robot'] = {}
        for name, flags in EftInfo._robot_flags.items():
            if params[0] & flag:
                metering['robot'][name] = True
            else:
                metering['robot'][name] = False
        metering['spdif'] = params[1]
        metering['adat'] = params[2]
        metering['outputs'] = []
        for i in range(params[5]):
            index = 9 + i
            if params[index] == 0:
                db = -144.0
            else:
                db = round(20 * log10(params[index] / 0x80000000), 1)
            metering['outputs'].append(db)
        metering['inputs'] = []
        for i in range(params[6]):
            index = 9 + params[5] + i
            if params[index] == 0:
                db = -144.0
            else:
                db = round(20 * log10(params[index] / 0x80000000), 1)
            metering['inputs'].append(db)
        return metering

    @staticmethod
    def set_resp_addr(unit, addr):
        args = get_array()
        args.append((addr >> 24) & 0xffffffff)
        args.append(addr         & 0xffffffff)
        EftInfo._execute_command(unit, 2, args)

    @staticmethod
    def read_session_data(unit, offset, quadlets):
        args = get_array()
        args.append(offset)
        args.append(quadlets)
        params = EftInfo._execute_command(unit, 3, args)
        return params

    @staticmethod
    def get_debug_info(unit):
        args = get_array()
        params = EftInfo._execute_command(unit, 4, args)

        # params[00]: isochronous stream 1 flushed
        # params[01]: isochronous stream 1 underruns
        # params[02]: firewire3 control
        # params[03]: firewire3 control written
        # params[04-15]: data
        return params

    @staticmethod
    def test_dsp(unit, value):
        args = get_array()
        args.append(value)
        params = EftInfo._execute_command(unit, 5, args)
        return params[0]

    @staticmethod
    def test_arm(unit, value):
        args = get_array()
        args.append(value)
        params = EftInfo._execute_command(unit, 6, args)
        return params[0]

    def _parse_capability(params):
        caps = {}
        for name, flag in EftInfo._feature_flags.items():
            if params[0] & flag:
                caps[name] = True
            else:
                caps[name] = False
        return caps

    def _parse_clock_source(params):
        srcs = {}
        for name, flag in EftInfo._clock_flags.items():
            if params[21] & flag:
                srcs[name] = True
            else:
                srcs[name] = False
        return srcs

    def _parse_sampling_rate(params):
        rates = {}
        for rate in EftInfo.supported_sampling_rates:
            if params[39] <= rate and rate <= params[38]:
                rates[rate] = True
            else:
                rates[rate] = False
        return rates

    def _parse_phys_ports(params):
        phys_outputs = []
        phys_inputs = []
        outputs = (params[27] >> 16, params[27] & 0xffff,
                   params[28] >> 16, params[28] & 0xffff,
                   params[29] >> 16, params[29] & 0xffff,
                   params[30] >> 16, params[30] & 0xffff)
        inputs = (params[32] >> 16, params[32] & 0xffff,
                  params[33] >> 16, params[33] & 0xffff,
                  params[34] >> 16, params[34] & 0xffff,
                  params[35] >> 16, params[35] & 0xffff)
        for i in range(params[26]):
            count = outputs[i] & 0xff
            index = outputs[i] >> 8
            if index > len(EftInfo.supported_port_names):
                name = 'dummy'
            else:
                name = EftInfo.supported_port_names[index]
            for j in range(count):
                phys_outputs.append(name)
        for i in range(params[31]):
            count = inputs[i] & 0xff
            index = inputs[i] >> 8
            if index > len(EftInfo.supported_port_names):
                name = 'dummy'
            else:
                name = EftInfo.supported_port_names[index]
            for j in range(count):
                phys_inputs.append(name)
        return {'phys-inputs': phys_inputs,
                'phys-outputs': phys_outputs}

    def _parse_mixer_channels(params):
        return {'capture-channels': params[43],
                'playback-channels': params[42]}

    def _parse_stream_formation(params):
        return {'tx-stream-channels': (params[23], params[46], params[48]),
                'rx-stream-channels': (params[22], params[45], params[47])}

    def _parse_firmware_versions(params):
        return {'DSP':  EftInfo._get_literal_version(params[40]),
                'ARM':  EftInfo._get_literal_version(params[41]),
                'FPGA': EftInfo._get_literal_version(params[44])}

    def _get_literal_version(val):
        return '{0}.{1}.{2}'.format((val >> 24) & 0xff, \
                                    (val >> 16) & 0xff, \
                                    (val >>  8) & 0xff)

#
# Category No.1, for flash commands
#
class EftFlash():
    def _execute_command(unit, cmd, args):
        if not isinstance(unit, Hinawa.SndEfw):
            raise ValueError('Invalid argument for SndEfw')
        return unit.transact(1, cmd, args)

    @staticmethod
    def erase(unit, offset):
        args = get_array()
        args.append(offset)
        EftFlash._execute_command(unit, 0, args)

    @staticmethod
    def read_block(unit, offset, quadlets):
        args = get_array()
        args.append(offset)
        args.append(quadlets)
        return EftFlash._execute_command(unit, 1, args)

    @staticmethod
    def write_block(unit, offset, data):
        args = get_array()
        args.append(offset)
        args.append(len(data))
        for datum in data:
            args.append(datum)
        EftFlash._execute_command(unit, 2, args)

    @staticmethod
    def get_status(unit):
        args = get_array()
        # return status means it.
        EftFlash._execute_command(unit, 3, args)

    @staticmethod
    def get_session_offset(unit):
        args = get_array()
        params = EftFlash._execute_command(unit, 4, args)
        return params[0]

    @staticmethod
    def set_lock(unit, lock):
        args = get_array()
        if lock is not 0:
            args.append(1)
        else:
            args.append(0)
        EftFlash._execute_command(unit, 5, args)

#
# Category No.2, for transmission control commands
#
class EftTransmit():
    supported_modes = ('windows', 'iec61883-6')
    supported_playback_drops = (1, 2, 4)
    supported_record_streatch_ratios = (1, 2, 4)
    supported_serial_bps = (16, 24)
    supported_serial_data_formats = ('left-adjusted', 'i2s')

    def _execute_command(unit, cmd, args):
        if not isinstance(unit, Hinawa.SndEfw):
            raise ValueError('Invalid argument for SndEfw')
        return unit.transact(2, cmd, args)

    @staticmethod
    def set_mode(unit, mode):
        if EftTransmit.supported_modes.count(mode) == 0:
            raise ValueError('Invalid argument for mode')
        args = get_array()
        args.append(EftTransmit.supported_modes.index(mode))
        EftTransmit._execute_command(unit, 0, args)

    @staticmethod
    def set_fw_hdmi(unit, playback_drop, record_stretch_ratio, serial_bps,
                    data_format):
        if EftTransmit.supported_playback_drops.count(playback_drop) == 0:
            raise ValueError('Invalid argument for playback drop')
        if EftTransmit.supported_record_streatch_ratios(record_stretch_ratio) == 0:
            raise ValueError('Invalid argument for record stretch')
        if EftTransmit.supported_serial_bps.count(serial_bps) == 0:
            raise ValueError('Invalid argument for serial bits per second')
        if EftTransmit.supported_serial_data_formats(serial_data_format) == 0:
            raise ValueError('Invalid argument for serial data format')

        args = get_array()
        args.append(playback_drop)
        args.append(record_stretch)
        args.append(serial_bps)
        args.append(EftTransmit.supported_serial_data_formats.index(serial_data_format))
        EftTransmit._execute_command(unit, 4, args)

#
# Category No.3, for hardware control commands
#
class EftHwctl():
    supported_box_states = (
        'internal-multiplexer',
        'spdif-pro',
        'spdif-non-audio',
        'control-room',
        'output-level-bypass',
        'metering-mode-in',
        'metering-mode-out',
        'soft-clip',
        'robot-hex-input',
        'robot-battery-charge',
        'phantom-powering'
    )

    # Internal parameters
    _box_state_params = {
        # identifier,         shift,        zero,       one
        'internal-multiplexer': ( 0, ('Disabled', 'Enabled')),
        'spdif-pro':            ( 1, ('Disabled', 'Enabled')),
        'spdif-non-audio':      ( 2, ('Disabled', 'Enabled')),
        'control-room':         ( 8, ('A', 'B')),
        'output-level-bypass':  ( 9, ('Disabled', 'Enabled')),
        'metering-mode-in':     (12, ('A', 'B')),
        'metering-mode-out':    (13, ('D1', 'D2')),
        'soft-clip':            (16, ('Disabled', 'Enabled')),
        'robot-hex-input':      (29, ('Disabled', 'Enabled')),
        'robot-battery-charge': (30, ('Disabled', 'Enabled')),
        'phantom-powering':     (31, ('Disabled', 'Enabled')),
    }

    @staticmethod
    def execute_command(unit, cmd, args):
        if not isinstance(unit, Hinawa.SndEfw):
            raise ValueError('Invalid argument for SndEfw')
        return unit.transact(3, cmd, args)

    @staticmethod
    def set_clock(unit, rate, source, reset):
        if EftInfo.supported_sampling_rates.count(rate) == 0:
            raise ValueError('Invalid argument for sampling rate')
        if EftHwctl.supported_clock_sources.count(source) == 0:
            raise ValueError('Invalid argument for source of clock')
        if reset > 0:
            reset = 0x80000000
        args = get_array()
        args.append(rate)
        args.append(EftHwctl.supported_clock_sources[source])
        args.append(reset)
        EftHwctl.execute_command(unit, 0, args)

    @staticmethod
    def get_clock(unit):
        args = get_array()
        params = EftHwctl.execute_command(unit, 1, args)
        if params[0] >= len(EftInfo.supported_clock_sources):
            raise OSError('Unexpected clock source in response')
        if EftInfo.supported_sampling_rates.count(params[1]) == 0:
            raise OSError('Unexpected sampling rate in response')
        return (params[1], EftInfo.supported_clock_sources[params[0]])

    @staticmethod
    def set_box_states(unit, states):
        enable = 0
        disable = 0
        for name,state in states:
            if name not in EftHwctl._box_state_params:
                raise ValueError('Invalid value in box states')
            shift   = EftHwctl._box_state_params[name][0]
            values  = EftHwctl._box_state_params[name][1]
            value = values.index(state)
            if value is 0:
                disabled |= (1 << shift)
            else:
                enabled |= (1 << shift)
        args = get_array()
        args.append(enabled)
        args.append(disabled)
        EftHwctl.execute_command(unit, 3, args)

    @staticmethod
    def get_box_states(unit):
        args = get_array()
        params = EftHwctl.execute_command(unit, 4, args)
        state = params[0]
        states = {}
        for name,params in EftHwctl._box_state_params.items():
            shift = params[0]
            values = params[1]
            index = (state >> shift) & 0x01
            states[name] = values[index]
        return states

    @staticmethod
    def reconnect_phy(unit):
        args = get_array()
        EftHwctl.execute_command(unit, 6, args)

    @staticmethod
    def blink_leds(unit):
        args = get_array()
        EftHwctl.execute_command(unit, 7, args)

    @staticmethod
    def set_continuous_clock(unit, continuous_rate):
        args = get_array()
        args.append(continuous_rate * 512 // 1500)
        EftHwctl.execute_command(unit, 8, args)

#
# Category No.4, for physical output multiplexer commands
#
class EftPhysOutput():
    operations = ('gain', 'mute', 'nominal')

    @staticmethod
    def execute_command(unit, cmd, args):
        if not isinstance(unit, Hinawa.SndEfw):
            raise ValueError('Invalid argument for SndEfw')
        return unit.transact(4, cmd, args)

    @staticmethod
    def set_param(unit, operation, channel, value):
        if operation is 'gain':
            cmd = 0
            value = calculate_vol_from_db(value)
        elif operation is 'mute':
            cmd = 2
            if value > 0:
                value = 1
        elif operation is 'nominal':
            cmd = 8
            if value > 0:
                value = 2
        else:
            raise ValueError('Invalid argument for operation.')
        args = get_array()
        args.append(channel)
        args.append(value)
        EftPhysOutput.execute_command(unit, cmd, args)

    @staticmethod
    def get_param(unit, operation, channel):
        if operation is 'gain':
            cmd = 1
        elif operation is 'mute':
            cmd = 3
        elif operation is 'nominal':
            cmd = 9
        else:
            raise ValueError('Invalid argument for operation.')
        args = get_array()
        args.append(channel)
        params = EftPhysOutput.execute_command(unit, cmd, args)
        if operation is 'gain':
            params[1] = calculate_vol_to_db(params[1])
        if operation is 'nominal':
            if params[1] == 2:
                params[1] = 1
        return params[1]

#
# Category No.5, for physical input multiplexer commands
#
class EftPhysInput():
    operations = ('nominal')

    def _execute_command(unit, cmd, args):
        if not isinstance(unit, Hinawa.SndEfw):
            raise ValueError('Invalid argument for SndEfw')
        return unit.transact(5, cmd, args)

    @staticmethod
    def set_param(unit, operation, channel, value):
        if operation is 'nominal':
            cmd = 8
            if value > 0:
                value = 2
        else:
            raise ValueError('Invalid argument for operation')
        args = get_array()
        args.append(channel)
        args.append(value)
        EftPhysInput._execute_command(unit, cmd, args)

    @staticmethod
    def get_param(unit, operation, channel):
        if operation is 'nominal':
            cmd = 9
        else:
            raise ValueError('Invalid argumentfor operation')
        args = get_array()
        args.append(channel)
        args.append(0xff)
        params = EftPhysInput._execute_command(unit, cmd, args)
        return params[1]

#
# Category No.6, for playback stream multiplexer commands
#
class EftPlayback():
    operations = ('gain', 'mute', 'solo')

    @staticmethod
    def execute_command(unit, cmd, args):
        if not isinstance(unit, Hinawa.SndEfw):
            raise ValueError('Invalid argument for SndEfw')
        return unit.transact(6, cmd, args)

    @staticmethod
    def set_param(unit, operation, channel, value):
        if operation is 'gain':
            cmd = 0
            value = calculate_vol_from_db(value)
        elif operation is 'mute':
            cmd = 2
            if value > 0:
                value = 1
        elif operation is 'solo':
            cmd = 4
            if value > 0:
                value = 1
        else:
            raise ValueError('Invalid argument for operation.')
        args = get_array()
        args.append(channel)
        args.append(value)
        EftPhysInput.execute_command(unit, cmd, args)

    @staticmethod
    def get_param(unit, operation, channel):
        if operation is 'gain':
            cmd = 1
        elif operation is 'mute':
            cmd = 3
        elif operation is 'solo':
            cmd = 5
        else:
            raise ValueError('Invalid argument for operation.')
        args = get_array()
        args.append(channel)
        params = EftPlayback.execute_command(unit, cmd, args)
        if operation is 'gain':
            params[1] = calculate_vol_to_db(params[1])
        return params[1]

class EftCapture():
    operations = ()

    @staticmethod
    def execute_command(unit, cmd, args):
        if not isinstance(unit, Hinawa.SndEfw):
            raise ValueError('Invalid argument for SndEfw')
        return unit.transact(7, cmd, args)

#
# Category No.8, for input monitoring multiplexer commands
#
class EftMonitor():
    operations = ('gain', 'mute', 'solo', 'pan')

    @staticmethod
    def execute_command(unit, cmd, args):
        if not isinstance(unit, Hinawa.SndEfw):
            raise ValueError('Invalid argument for SndEfw')
        return unit.transact(8, cmd, args)

    @staticmethod
    def set_param(unit, operation, in_ch, out_ch, value):
        if operation is 'gain':
            cmd = 0
            value = calculate_vol_from_db(value)
        elif operation is 'mute':
            cmd = 2
            if value > 0:
                value = 1
        elif operation is 'solo':
            cmd = 4
            if value > 0:
                value = 1
        elif operation is 'pan':
            cmd = 6
            if value < 0 or value > 255:
                raise ValueError('Invalid argument for panning')
        else:
            raise ValueError('Invalid argument for operation.')
        args = get_array()
        args.append(in_ch)
        args.append(out_ch)
        args.append(value)
        EftMonitor.execute_command(unit, cmd, args)

    @staticmethod
    def get_param(unit, operation, in_ch, out_ch):
        if operation is 'gain':
            cmd = 1
        elif operation is 'mute':
            cmd = 3
        elif operation is 'solo':
            cmd = 5
        elif operation is 'pan':
            cmd = 7
        else:
            raise ValueError('Invalid argument for operation.')
        args = get_array()
        args.append(in_ch)
        args.append(out_ch)
        params = EftMonitor.execute_command(unit, cmd, args)
        if operation is 'gain':
            params[2] = calculate_vol_to_db(params[2])
        return params[2]

#
# Category No.9, for input/output configuration commands
#
class EftIoconf():
    # NOTE: use the same strings in features of EftInfo.
    digital_input_modes = ('spdif-coax', 'aesebu-xlr', 'spdif-opt', 'adat-opt')

    def _execute_command(unit, cmd, args):
        if not isinstance(unit, Hinawa.SndEfw):
            raise ValueError('Invalid argument for SndEfw')
        return unit.transact(9, cmd, args)

    @staticmethod
    def set_control_room_mirroring(unit, output_pair):
        args = get_array()
        args.append(output_pair)
        EftIoconf._execute_command(unit, 0, args)

    @staticmethod
    def get_control_room_mirroring(unit):
        args = get_array()
        params = EftIoconf._execute_command(unit, 1, args)
        return params[0]

    @staticmethod
    def set_digital_input_mode(unit, mode):
        if EftIoconf.digital_input_modes.count(mode) == 0:
            raise ValueError('Invalid argument for digital mode')
        args = get_array()
        args.append(EftIoconf.digital_input_modes.index(mode))
        params = EftIoconf._execute_command(unit, 2, args)

    @staticmethod
    def get_digital_input_mode(unit):
        args = get_array()
        params = EftIoconf._execute_command(unit, 3, args)
        if params[0] >= len(EftIoconf.digital_input_modes):
            raise OSError
        return EftIoconf.digital_input_modes[params[0]]

    @staticmethod
    def set_phantom_powering(unit, state):
        if state > 0:
            state = 1
        args = get_array()
        args.append(state)
        EftIoconf._execute_command(unit, 4, args)

    @staticmethod
    def get_phantom_powering(unit):
        args = get_array()
        params= EftIoconf._execute_command(unit, 5, args)
        return params[0]

    @staticmethod
    def set_stream_mapping(unit, rx_maps, tx_maps):
        args = get_array()
        params = EftIoconf._execute_command(unit, 6, args)
        rx_map_count = params[2]
        if len(rx_maps) > rx_map_count:
            ValueError('Invalid argument for rx stream mapping')
        tx_map_count = params[34]
        if len(tx_maps) > tx_map_count:
            ValueError('Invalid argument for tx stream mapping')
        for i in range(rx_maps):
            params[4 + i] = rx_maps[i]
        for i in range(tx_maps):
            params[36 + i] = tx_maps[i]
        EftIoconf._execute_command(unit, 6, args)

    @staticmethod
    def get_stream_mapping(unit):
        args = get_array()
        param = EftIoconf._execute_command(unit, 7, args)
        tx_map_count = param[34]
        tx_map = []
        for i in range(tx_map_count):
            tx_map.append(param[36 + i])
        rx_map_count = param[2]
        rx_map = []
        for i in range(rx_map_count):
            rx_map.append(param[4 + i])
        return {'tx-map': tx_map, 'rx-map': rx_map}
