from ta1394.general import AvcGeneral
from ta1394.streamformat import AvcStreamFormatInfo

import time

class BcoPlugInfo():
    addr_dir  = ('input', 'output')
    addr_mode = ('unit', 'subunit', 'function-block')
    addr_unit_type = ('isoc', 'external', 'async')

    plug_type = ('IsoStream', 'AsyncStream', 'MIDI', 'Sync', 'Analog',
                 'Digital', 'Clock')
    ch_location = ('N/A', 'left-front', 'right-front', 'center', 'subwoofer',
                   'left-surround', 'right-surround', 'left-of-center',
                   'right-of-center', 'surround', 'side-left', 'side-right',
                   'top', 'buttom', 'left-front-effect', 'right-front-effect',
                   'no-position')
    port_type = ('speaker', 'headphone', 'microphone', 'line', 'spdif',
                 'adat', 'tdif', 'madi', 'analog', 'digital', 'MIDI', 'no-type')

    @staticmethod
    def get_unit_addr(addr_dir, addr_unit_type, plug):
        if BcoPlugInfo.addr_dir.count(addr_dir) == 0:
            raise ValueError('Invalid argument for address direction')
        if BcoPlugInfo.addr_unit_type.count(addr_unit_type) == 0:
            raise ValueError('Invalid argumetn for address unit type')
        if plug > 255:
            raise ValueError('Invalid argument for plug number')
        addr = bytearray()
        addr.append(BcoPlugInfo.addr_dir.index(addr_dir))
        addr.append(BcoPlugInfo.addr_mode.index('unit'))
        addr.append(BcoPlugInfo.addr_unit_type.index(addr_unit_type))
        addr.append(plug)
        addr.append(0xff)
        # For my purpose.
        addr.append(0xff)
        return addr

    @staticmethod
    def get_subunit_addr(addr_dir, subunit_type, subunit_id, plug):
        if BcoPlugInfo.addr_dir.count(addr_dir) == 0:
            raise ValueError('Invalid argument for address direction')
        if AvcGeneral.subunit_types.count(subunit_type) == 0:
            raise ValueError('Invalid argument for address subunit type')
        if subunit_id > 7:
            raise ValueError('Invalid argument for address subunit id')
        if plug > 255:
            raise ValueError('Invalid argument for address plug number')
        addr = bytearray()
        addr.append(BcoPlugInfo.addr_dir.index(addr_dir))
        addr.append(BcoPlugInfo.addr_mode.index('subunit'))
        addr.append(plug)
        addr.append(0xff)
        addr.append(0xff)
        # For my purpose.
        addr.append((AvcGeneral.subunit_types.index(subunit_type) << 3) | \
                    subunit_id)
        return addr

    @staticmethod
    def get_function_block_addr(addr_dir, subunit_type, subunit_id,
                                fb_type, fb_id, plug):
        if BcoPlugInfo.addr_dir.count(addr_dir) == 0:
            raise ValueError('Invalid argument for address direction')
        if AvcGeneral.subunit_types.count(subunit_type) == 0:
            raise ValueError('Invalid argument for address subunit type')
        if subunit_id > 7:
            raise ValueError('Invalid argument for address subunit id')
        addr = bytearray()
        addr.append(BcoPlugInfo.addr_dir.index(addr_dir))
        addr.append(BcoPlugInfo.addr_mode.index('function-block'))
        addr.append(fb_type)
        addr.append(fb_id)
        addr.append(plug)
        # For my purpose.
        addr.append((AvcGeneral.subunit_types.index(subunit_type) << 3) | \
                    subunit_id)
        return addr

    @staticmethod
    def build_plug_info(info):
        addr = bytearray()
        if BcoPlugInfo.addr_dir.count(info['dir']) == 0:
            raise ValueError('Invalid address direction')
        addr.append(BcoPlugInfo.addr_dir.index(info['dir']))
        if BcoPlugInfo.addr_mode.count(info['mode']) == 0:
            raise ValueError('Invalid address mode')
        addr.append(BcoPlugInfo.addr_mode.index(info['mode']))
        data = info['data']
        if info['mode'] == 'unit':
            if BcoPlugInfo.addr_unit_type.count(data['unit-type']) == 0:
                raise ValueError('Invalid address unit type')
            addr.append(BcoPlugInfo.addr_unit_type.index(data['unit-type']))
            addr.append(data['plug'])
            addr.append(0xff)
            addr.append(0xff)
            addr.append(0xff)
        else:
            if AvcGeneral.subunit_types.count(data['subunit-type']) == 0:
                raise ValueError('Invalid address subunit type')
            addr.append(AvcGeneral.subunit_types.index(data['subunit-type']))
            addr.append(data['subunit-id'])
            addr.append(0xff)
            addr.append(0xff)
            if info['mode'] is 'function-block':
                addr.append(data['function-block-type'])
                addr.append(data['function-block-id'])
                addr.append(data['plug'])
        return addr

    @staticmethod
    def parse_plug_addr(addr):
        info = {}
        if addr[0] == 0xff:
            return info
        if addr[0] >= len(BcoPlugInfo.addr_dir):
            raise OSError('Unexpected address direction')
        info['dir'] = BcoPlugInfo.addr_dir[addr[0]]
        if addr[1] >= len(BcoPlugInfo.addr_mode):
            raise OSError('Unexpected address mode in response')
        info['mode'] = BcoPlugInfo.addr_mode[addr[1]]
        data = {}
        if info['mode'] == 'unit':
            if addr[2] >= len(BcoPlugInfo.addr_unit_type):
                raise OSError('Unexpected address unit type in response')
            data['unit-type'] = BcoPlugInfo.addr_unit_type[addr[2]]
            data['plug'] = addr[3]
        else:
            if addr[2] >= len(AvcGeneral.subunit_types):
                raise OSError('Unexpected address subunit type in response')
            data['subunit-type'] = AvcGeneral.subunit_types[addr[2]]
            data['subunit-id'] = addr[3]
            if info['mode'] == 'subunit':
                data['plug'] = addr[4]
            if info['mode'] == 'function-block':
                data['function-block-type'] = addr[4]
                data['function-block-id'] = addr[5]
                data['plug'] = addr[6]
        info['data'] = data
        return info

    @staticmethod
    def get_plug_type(unit, addr):
        args = bytearray()
        args.append(0x01)
        args.append(addr[5])
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Bco plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x00)   # Info type is 'type'
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        if params[10] > len(BcoPlugInfo.plug_type):
            raise OSError('Unexpected value in response')
        return BcoPlugInfo.plug_type[params[10]]

    @staticmethod
    def get_plug_name(unit, addr):
        args = bytearray()
        args.append(0x01)
        args.append(addr[5])
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Bco plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x01)   # Info type is 'name'
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        length = params[10]
        if length == 0:
            return ""
        return params[11:11 + length].decode()

    @staticmethod
    def get_plug_channels(unit, addr):
        args = bytearray()
        args.append(0x01)
        args.append(addr[5])
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Bco plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x02)   # Info type is 'the number of channels'
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        return params[10]

    @staticmethod
    def get_plug_ch_name(unit, addr, pos):
        args = bytearray()
        args.append(0x01)
        args.append(addr[5])
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Bco plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x04)   # Info type is 'channel position name'
        args.append(pos)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        length = params[11]
        return params[12:12+length].decode()

    @staticmethod
    def get_plug_clusters(unit, addr):
        if addr[1] != BcoPlugInfo.addr_mode.index('unit') or \
           addr[2] != BcoPlugInfo.addr_unit_type.index('isoc'):
            raise ValueError('Isochronous unit plugs just support this')
        args = bytearray()
        args.append(0x01)
        args.append(addr[5])
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Bco plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x03)   # Info type is 'channel position data'
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        data = params[10:]
        pos = 0
        clusters = [[] for i in range(data[pos])]
        pos += 1
        for cls in range(len(clusters)):
            num = data[pos]
            pos += 1
            if num == 0:
                break;

            clusters[cls] = [[0, 0] for j in range(num)]
            for e in range(len(clusters[cls])):
                clusters[cls][e][0] = data[pos];
                clusters[cls][e][1] = data[pos + 1];
                pos += 2
        return clusters

    @staticmethod
    def get_plug_cluster_info(unit, addr, cls):
        if addr[1] != BcoPlugInfo.addr_mode.index('unit') or \
           addr[2] != BcoPlugInfo.addr_unit_type.index('isoc'):
            raise ValueError('Isochronous unit plugs just support this')
        args = bytearray()
        args.append(0x01)
        args.append(addr[5])
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Bco plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x07)   # Info type is 'cluster info'
        args.append(cls)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        length = params[12]
        return params[13:13+length].decode()

    @staticmethod
    def get_plug_input(unit, addr):
        args = bytearray()
        args.append(0x01)
        args.append(addr[5])
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Bco plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x05)   # Info type is 'input data'
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        return BcoPlugInfo.parse_plug_addr(params[10:])

    @staticmethod
    def get_plug_outputs(unit, addr):
        args = bytearray()
        args.append(0x01)
        args.append(addr[5])
        args.append(0x02)   # Plug info command
        args.append(0xc0)   # Bco plug info subcommand
        args.append(addr[0])
        args.append(addr[1])
        args.append(addr[2])
        args.append(addr[3])
        args.append(addr[4])
        args.append(0x06)   # Info type is 'output data'
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        info = []
        plugs = params[10]
        if plugs != 0xff:
            for i in range(plugs):
                addr = BcoPlugInfo.parse_plug_addr(params[11 + i * 7:])
                info.append(addr)
        return info

class BcoSubunitInfo():
    fb_purpose = {
        0x00: 'input-gain',
        0x01: 'output-volume',
        0xff: 'nothing-special'
    }

    @staticmethod
    def get_subunits(unit):
        args = bytearray()
        args.append(0x01)
        args.append(0xff)
        args.append(0x31)
        args.append(0x00)   # Any values are approved.
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        args.append(0xff)
        params = AvcGeneral.command_status(unit, args)
        subunits = []
        for i in range(4, 7):
            if params[i] is not 0xff:
                subunit = {}
                subunit['type'] = AvcGeneral.subunit_types[params[i] >> 3]
                subunit['id'] = params[i] & 0x7
                subunits.append(subunit)
        return subunits

    @staticmethod
    def get_subunit_fb_info(unit, subunit_type, subunit_id, page, fb_type):
        if AvcGeneral.subunit_types.count(subunit_type) == 0:
            raise ValueError('Invalid argument for subunit type')
        if subunit_id > 7:
            raise ValueError('Invalid argument for subunit id')
        args = bytearray(0xff for i in range(29))
        args[0] = 0x01
        args[1] = (AvcGeneral.subunit_types.index(subunit_type) << 3) | subunit_id
        args[2] = 0x31
        args[3] = page
        args[4] = 0xff
        params = AvcGeneral.command_status(unit, args)
        entries = []
        for i in range(5):
            if params[5 + 5 * i] == 0xff:
                continue
            entry = {}
            entry['fb-type'] = params[5 + 5 * i]
            entry['fb-id'] = params[6 + 5 * i]
            entry['fb-purpose'] = BcoSubunitInfo.fb_purpose[params[7 + 5 * i]]
            entry['inputs'] = params[8+ 5 * i]
            entry['outputs'] = params[9 + 5 * i]
            entries.append(entry)
        return entries

class BcoVendorDependent():
    supported_spec = ('con', 'pro')
    addr_dir = ('input', 'output')

    # For IEC 60958-1, a.k.a. 'concumer' or 'S/PDIF'
    supported_con_status = {
        # name, the number of values
        'consumerUse':             1,
        'linearPCM':               1,
        'copyRight':               1,
        'additionalFormatInfo':    1,
        'channelStatusMode':       1,
        'categoryCode':            1,
        'sourceNumber':            1,
        'channelNumber':           1,
        'samplingFrequency':       1,
        'clkAccuracy':             1,
        'maxWordLength':           1,
        'sampleWordLength':        1,
    }

    # For IEC 60958-3, a.k.a 'professional' or 'AES'
    supported_pro_status = {
        # name, the number of values
        'profesionalUse':          1,
        'linearPCM':               1,
        'audioSignalEmphasis':     1,
        'srcSampleFreqLock':       1,
        'samplingFrequency':       1,
        'channelMode':             1,
        'userBitManagement':       1,
        'auxSampleBitsUse':        1,
        'sourceWordLength':        1,
        'multiChannelDesc':        1,
        'referenceSignal':         1,
        'refSigSamplFreq':         1,
        'scalingFlag':             1,
        'channelOriginData':       4,
        'channelDestData':         4,
        'localSampleAddrCode':     4,
        'timeOfDaySampleAddrCode': 4,
        'reliabilityFlags':        1,
        'cyclicRedundancyCheck':   1,
    }

    _con_subcmds = {
        'consumerUse':             0x00,
        'linearPCM':               0x01,
        'copyRight':               0x02,
        'additionalFormatInfo':    0x03,
        'channelStatusMode':       0x04,
        'categoryCode':            0x05,
        'sourceNumber':            0x06,
        'channelNumber':           0x07,
        'samplingFrequency':       0x08,
        'clkAccuracy':             0x09,
        'maxWordLength':           0x0a,
        'sampleWordLength':        0x0b,
    }

    _pro_subcmds = {
        'profesionalUse':          0x00,
        'linearPCM':               0x01,
        'audioSignalEmphasis':     0x02,
        'srcSampleFreqLock':       0x03,
        'samplingFrequency':       0x04,
        'channelMode':             0x05,
        'userBitManagement':       0x06,
        'auxSampleBitsUse':        0x07,
        'sourceWordLength':        0x08,
        'multiChannelDesc':        0x09,
        'referenceSignal':         0x0a,
        'refSigSamplFreq':         0x0b,
        'scalingFlag':             0x0c,
        'channelOriginData':       0x0d,
        'channelDestData':         0x0e,
        'localSampleAddrCode':     0x0f,
        'timeOfDaySampleAddrCode': 0x10,
        'reliabilityFlags':        0x11,
        'cyclicRedundancyCheck':   0x12,
    }

    @staticmethod
    def set_digital_channel_status(unit, spec, name, values):
        if   spec is 'con':
            attrs = BcoVendorDependent.supported_con_status
            subcmds  = BcoVendorDependent._con_subcmds
        elif spec is 'pro':
            attrs = BcoVendorDependent.supported_pro_status
            subcmds = BcoVendorDependent._pro_subcmds
        else:
            raise ValueError('Invalid argument for specification name')
        if name not in attrs:
            raise ValueError('Invalid argument for attribute name')
        if attrs[name] != 1:
            if type(values) is not 'list' or len(values) != attrs[name]:
                raise ValueError('Invalid argument for attribute value length')
        args = bytearray(0xff for i in range(10))
        args[0] = 0x00
        args[1] = 0xff
        args[2] = 0x00
        args[3] = BcoVendorDependent.supported_spec.index(spec)
        args[4] = subcmds[name]
        args[5] = attrs[name]
        if attrs[name] == 1:
            args[6] = values
        else:
            for i in range(len(values)):
                args[6 + i] = values[i]
        AvcGeneral.command_control(unit, args)

    def get_digital_channel_status(unit, spec, name):
        if   spec is 'con':
            attrs = BcoVendorDependent.supported_con_status
            subcmds  = BcoVendorDependent._con_subcmds
        elif spec is 'pro':
            attrs = BcoVendorDependent.supported_pro_status
            subcmds = BcoVendorDependent._pro_subcmds
        else:
            raise ValueError('Invalid argument for specification name')
        if name not in attrs:
            raise ValueError('Invalid argumetn for attribute name')
        args = bytearray(0xff for i in range(10))
        args[0] = 0x01
        args[1] = 0xff
        args[2] = 0x00
        args[3] = BcoVendorDependent.supported_spec.index(spec)
        args[4] = subcmds[name]
        args[5] = attrs[name]
        params = AvcGeneral.command_status(unit, args)
        return params[6:6 + attrs[name]]

    def get_stream_detection(self, company_ids, dir, ext_plug):
        if BcoVendorDependent.addr_dir.count(dir) == 0:
            raise ValueError('Invalid argument for address direction')
        if ext_plug >= 255:
            raise ValueError('Invalid argument for external plug number')
        args = bytearray()
        args.append(0x00)
        args.append(BcoVendorDependent.addr_dir.index(dir))
        args.append(plug)
        args.append(0x00)
        params = AvcGeneral.get_vendor_dependent(self, company_ids, args)
        if params[0] != args[0] or params[1] != args[1] or params[2] != args[2]:
            raise OSError('Unexpected value in response')
        if params[3] == 0x00:
            return False
        return True

class BcoStreamFormatInfo():
    format_types = ('Compound', 'Sync')
    data_types = ('IEC60958-3',     # 0x00
                  'IEC61937-3',
                  'IEC61937-4',
                  'IEC61937-5',
                  'IEC61937-6',
                  'IEC61937-7',
                  'multi-bit-linear-audio-raw',
                  'multi-bit-linear-audio-DVD-audio',
                  'one-bit-audio-plain-raw',
                  'one-bit-audio-plain-SACD',
                  'one-bit-audio-encoded-raw',
                  'one-bit-audio-encoded-SACD',
                  'high-precision-multi-bit-linear-audio',
                  'MIDI-conformant',
                  'sync-stream',    # 0x40
                  'do-not-care',    # 0xff
                  'reserved')       # the others

    @staticmethod
    def get_entry_list(fcp, addr):
        fmts = []
        for i in range(0xff):
            # DM1500 tends to cause timeout.
            time.sleep(0.1)
            try:
                args = bytearray()
                args.append(0x01)
                args.append(addr[5])
                args.append(0x2f)   # Bco stream format support
                args.append(0xc1)   # List request
                args.append(addr[0])
                args.append(addr[1])
                args.append(addr[2])
                args.append(addr[3])
                args.append(addr[4])
                args.append(0xff)
                args.append(i)
                args.append(0xff)
                params = AvcGeneral.command_status(fcp, args)
                fmts.append(BcoStreamFormatInfo._parse_format(params[11:]))
            except OSError as e:
                if str(e) != 'Rejected':
                    raise
                else:
                    break
        return fmts

    # Two types of sync stream: 0x90/0x00/0x40 and 0x90/0x40 with 'sync-stream'
    @staticmethod
    def _parse_format(params):
        fmt = {}
        # Sync stream with stereo raw audio
        if params[0] == 0x90 and params[1] == 0x00 and params[2] == 0x40:
            ctl = params[4] & 0x01
            rate = params[4] >> 8
            fmt['type'] = 'Sync'
            fmt['rate-control'] = AvcStreamFormatInfo.rate_controls[ctl]
            fmt['sampling-rate'] = AvcStreamFormatInfo.sampling_rates[rate]
            fmt['formation'] = ['multi-bit-linear-audio-raw']
            return fmt
        if params[0] != 0x90 or params[1] != 0x40:
            raise RuntimeError('Unsupported format')
        fmt['type'] = 'Compound'
        fmt['sampling-rate'] = AvcStreamFormatInfo.sampling_rates[params[2]]
        ctl = params[3] & 0x3
        fmt['rate-control'] = AvcStreamFormatInfo.rate_controls[ctl]
        formation = []
        for i in range(params[4]):
            for c in range(params[5 + i * 2]):
                type = params[5 + i * 2 + 1]
                if type <= 0x0f:
                    formation.append(BcoStreamFormatInfo.data_types[type])
                elif type == 0x40:
                    formation.append('sync-stream')
                elif type == 0xff:
                    formation.append('do-not-care')
                else:
                    formation.append('reserved')
        fmt['formation'] = formation
        return fmt
