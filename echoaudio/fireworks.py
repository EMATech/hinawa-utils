from gi.repository import Hinawa
from echoaudio.transactions import EftInfo
from echoaudio.transactions import EftHwctl
from echoaudio.transactions import EftPhysOutput
from echoaudio.transactions import EftPhysInput
from echoaudio.transactions import EftPlayback
from echoaudio.transactions import EftMonitor
from echoaudio.transactions import EftIoconf

class Fireworks(Hinawa.SndEfw):
    info = {}

    def __init__(self, card):
        super().__init__()
        self.open('/dev/snd/hwC{0}D0'.format(card))
        self.listen()
        self.info = EftInfo.get_spec(self)

    def get_metering(self):
        return EftInfo.get_metering(self)

    def set_clock_state(self, rate, src):
        EftHwctl.set_clock(self, rate, src, 0)
    def get_clock_state(self):
        return EftHwctl.get_clock(self)
    def set_box_states(self, name, state):
        states = EftHwctl.get_box_states(self)
        states[name] = state
        EftHwctl.set_box_states(self, states)
    def get_box_states(self):
        states = {}
        state_all = EftHwctl.get_box_states(self)
        if self.info['features']['spdif-coax'] or \
           self.info['features']['spdif-opt']:
            states['spdif-pro'] = state_all['spdif-pro']
            states['spdif-non-audio'] = state_all['spdif-non-audio']
        if self.info['features']['control-room-mirroring']:
            states['control-room'] = state_all['control-room']
            states['output-level-bypass'] = state_all['output-level-bypass']
            states['metering-mode-in'] = state_all['metering-mode-in']
            states['metering-mode-out'] = state_all['metering-mode-out']
        if self.info['features']['soft-clip']:
            states['soft-clip'] = state_all['soft-clip']
        if self.info['features']['robot-hex-input']:
            states['robot-hex-input'] = state_all['robot-hex-input']
        if self.info['features']['robot-battery-charge']:
            states['robot-battery-charge'] = state_all['robot-battery-charge']
        states['internal-multiplexer'] = state_all['internal-multiplexer']
        return states

    def set_phys_out_gain(self, ch, val):
        if ch >= len(self.info['phys-outputs']):
            raise ValueError('Invalid argument for physical output channel')
        EftPhysOutput.set_param(self, 'gain', ch, val)
    def get_phys_out_gain(self, ch):
        if ch >= len(self.info['phys-outputs']):
            raise ValueError('Invalid argument for physical output channel')
        return EftPhysOutput.get_param(self, 'gain', ch)
    def set_phys_out_mute(self, ch, val):
        if ch >= len(self.info['phys-outputs']):
            raise ValueError('Invalid argument for physical output channel')
        EftPhysOutput.set_param(self, 'mute', ch, val)
    def get_phys_out_mute(self, ch):
        if ch >= len(self.info['phys-outputs']):
            raise ValueError('Invalid argument for physical output channel')
        return EftPhysOutput.get_param(self, 'mute', ch)
    def set_phys_out_nominal(self, ch, val):
        if ch >= len(self.info['phys-outputs']):
            raise ValueError('Invalid argument for physical output channel')
        EftPhysOutput.set_param(self, 'nominal', ch, val)
    def get_phys_out_nominal(self, ch):
        if ch >= len(self.info['phys-outputs']):
            raise ValueError('Invalid argument for physical output channel')
        return EftPhysOutput.get_param(self, 'nominal', ch)

    def set_phys_in_nominal(self, ch, val):
        if ch >= len(self.info['phys-inputs']):
            raise ValueError('Invalid argument for physical input channel')
        EftPhysInput.set_param(self, 'nominal', ch, val)
    def get_phys_in_nominal(self, ch):
        if ch >= len(self.info['phys-inputs']):
            raise ValueError('Invalid argument for physical input channel')
        return EftPhysInput.get_param(self, 'nominal', ch)

    def set_playback_gain(self, ch, val):
        if ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        EftPlayback.set_param(self, 'gain', ch, val)
    def get_playback_gain(self, ch):
        if ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        return EftPlayback.get_param(self, 'gain', ch)
    def set_playback_mute(self, ch, val):
        if ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        EftPlayback.set_param(self, 'mute', ch, val)
    def get_playback_mute(self, ch):
        if ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        return EftPlayback.get_param(self, 'mute', ch)
    def set_playback_solo(self, ch, val):
        if ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        EftPlayback.set_param(self, 'solo', ch, val)
    def get_playback_solo(self, ch):
        if ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        return EftPlayback.get_param(self, 'solo', ch)

    def set_monitor_gain(self, in_ch, out_ch, val):
        if in_ch >= self.info['capture-channels']:
            raise ValueError('Invalid argument for capture channel')
        if out_ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        EftMonitor.set_param(self, 'gain', in_ch, out_ch, val)
    def get_monitor_gain(self, in_ch, out_ch):
        if in_ch >= self.info['capture-channels']:
            raise ValueError('Invalid argument for capture channel')
        if out_ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        return EftMonitor.get_param(self, 'gain', in_ch, out_ch)
    def set_monitor_mute(self, in_ch, out_ch, val):
        if in_ch >= self.info['capture-channels']:
            raise ValueError('Invalid argument for capture channel')
        if out_ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        EftMonitor.set_param(self, 'mute', in_ch, out_ch, val)
    def get_monitor_mute(self, in_ch, out_ch):
        if in_ch >= self.info['capture-channels']:
            raise ValueError('Invalid argument for capture channel')
        if out_ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        return EftMonitor.get_param(self, 'mute', in_ch, out_ch)
    def set_monitor_solo(self, in_ch, out_ch, val):
        if in_ch >= self.info['capture-channels']:
            raise ValueError('Invalid argument for capture channel')
        if out_ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        EftMonitor.set_param(self, 'solo', in_ch, out_ch, val)
    def get_monitor_solo(self, in_ch, out_ch):
        if in_ch >= self.info['capture-channels']:
            raise ValueError('Invalid argument for capture channel')
        if out_ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        return EftMonitor.get_param(self, 'solo', in_ch, out_ch)
    def set_monitor_pan(self, in_ch, out_ch, val):
        if in_ch >= self.info['capture-channels']:
            raise ValueError('Invalid argument for capture channel')
        if out_ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        EftMonitor.set_param(self, 'pan', in_ch, out_ch, val)
    def get_monitor_pan(self, in_ch, out_ch):
        if in_ch >= self.info['capture-channels']:
            raise ValueError('Invalid argument for capture channel')
        if out_ch >= self.info['playback-channels']:
            raise ValueError('Invalid argument for playback channel')
        return EftMonitor.get_param(self, 'pan', in_ch, out_ch)

    def set_control_room_mirroring(self, output_pair):
        if self.info['features']['control-room-mirroring'] is False:
            raise RuntimeError('Not supported by this model')
        EftIoconf.set_control_room_mirroring(self, output_pair)
    def get_control_room_mirroring(self):
        if self.info['features']['control-room-mirroring'] is False:
            raise RuntimeError('Not supported by this model')
        return EftIoconf.get_control_room_mirroring(self)
    def set_digital_input_mode(self, mode):
        if self.info['features'][mode] is False:
            raise RuntimeError('Not supported by this model')
        EftIoconf.set_digital_input_mode(self, mode)
    def get_digital_input_mode(self):
        return EftIoconf.get_digital_input_mode(self)
    def set_phantom_powering(self, state):
        if self.info['features']['phantom-powering'] is False:
            raise RuntimeError('Not supported by this model')
        EftIoconf.set_phantom_powering(self, state)
    def get_phantom_powering(self):
        if self.info['features']['phantom-powering'] is False:
            raise RuntimeError('Not supported by this model')
        return EftIoconf.get_phantom_powering(self)
    def set_stream_mapping(self, rx_maps, tx_maps):
        if rx_maps and self.info['features']['rx-mapping'] is False:
            raise RuntimeError('Not supported by this model')
        if tx_maps and self.info['features']['tx-mapping'] is False:
            raise RuntimeError('Not supported by this model')
        EftIoconf.set_stream_mapping(self, rx_maps, tx_maps)
    def get_stream_mapping(self):
        if self.info['features']['rx-mapping'] is False and \
           self.info['features']['tx-mapping'] is False:
            raise RuntimeError('Not supported by this model')
        return EftIoconf.get_stream_mapping(self)
