from gi.repository import Hinawa

from ta1394.general import AvcGeneral
from ta1394.general import AvcConnection
from ta1394.ccm import AvcCcm

from bridgeco.extensions import BcoPlugInfo
from bridgeco.extensions import BcoSubunitInfo
from bridgeco.extensions import BcoStreamFormatInfo

class BebobNormal(Hinawa.FwUnit):
    unit_info = {}
    unit_plugs = {}
    subunit_plugs = {}
    signal_destination = {}
    signal_sources = {}

    def __init__(self, path):
        super().__init__()
        self.open(path)
        self.listen()

        fcp = Hinawa.FwFcp()
        fcp.listen(self)

        self.unit_info = self._parse_unit_info(fcp)
        self.unit_plugs = self._parse_unit_plugs(fcp)

        self.subunit_plugs = self._parse_subunit_plugs(fcp)

        self.function_block_plugs = self._parse_function_block_plugs(fcp)

        self.stream_formats = self._parse_stream_formats(fcp)

        self.signal_destination = self._parse_signal_destination(fcp)
        self.signal_sources = self._parse_signal_sources(fcp)

        fcp.unlisten()
        del fcp

    def _parse_unit_info(self, fcp):
        return AvcGeneral.get_unit_info(fcp) 

    def _parse_unit_plugs(self, fcp):
        unit_plugs = {}
        info = AvcConnection.get_unit_plug_info(fcp)
        for type, params in info.items():
            if type not in unit_plugs:
                unit_plugs[type] = {}
            for dir, num in params.items():
                if dir not in unit_plugs[type]:
                    unit_plugs[type][dir] = []
                for i in range(num):
                    plug = self._parse_unit_plug(fcp, dir, type, i)
                    unit_plugs[type][dir].append(plug)
        return unit_plugs

    def _parse_unit_plug(self, fcp, dir, type, num):
        plug = {}
        addr = BcoPlugInfo.get_unit_addr(dir, type, num)
        plug['type'] = BcoPlugInfo.get_plug_type(fcp, addr)
        plug['name'] = BcoPlugInfo.get_plug_name(fcp, addr)
        plug['channels'] = []
        channels = BcoPlugInfo.get_plug_channels(fcp, addr)
        for channel in range(channels):
            ch = BcoPlugInfo.get_plug_ch_name(fcp, addr, channel + 1)
            plug['channels'].append(ch)
        plug['clusters'] = []
        if plug['type'] is 'IsoStream':
            clusters = BcoPlugInfo.get_plug_clusters(fcp, addr)
            for cluster in range(len(clusters)):
                clst = BcoPlugInfo.get_plug_cluster_info(fcp, addr, cluster + 1)
                plug['clusters'].append(clst)
        plug['input'] = []
        plug['outputs'] = []
        if dir == 'output':
            plug['input'] = BcoPlugInfo.get_plug_input(fcp, addr)
        else:
            plug['outputs'] = BcoPlugInfo.get_plug_outputs(fcp, addr)
        return plug

    def _parse_subunit_plugs(self, fcp):
        subunit_plugs = {}
        subunits = BcoSubunitInfo.get_subunits(fcp)
        for subunit in subunits:
            type = subunit['type']
            id = subunit['id']
            if subunit['id'] != 0:
                raise RuntimeError('Unsupported number for subunit id')
            if type not in subunit_plugs:
                subunit_plugs[type] = {}
                subunit_plugs[type]['input'] = []
                subunit_plugs[type]['output'] = []
            info = AvcConnection.get_subunit_plug_info(fcp, type, 0)
            for dir, num in info.items():
                for i in range(num):
                    plug = self._parse_subunit_plug(fcp, dir, type, 0, i)
                    subunit_plugs[type][dir].append(plug)
        return subunit_plugs

    def _parse_subunit_plug(self, fcp, dir, type, id, num):
        plug = {}
        addr = BcoPlugInfo.get_subunit_addr(dir, type, id, num)
        plug['type'] = BcoPlugInfo.get_plug_type(fcp, addr)
        plug['name'] = BcoPlugInfo.get_plug_name(fcp, addr)
        plug['channels'] = []
        channels = BcoPlugInfo.get_plug_channels(fcp, addr)
        for channel in range(channels):
            ch = BcoPlugInfo.get_plug_ch_name(fcp, addr, channel + 1)
            plug['channels'].append(ch)
        plug['clusters'] = []
        if plug['type'] is 'IsoStream':
            clusters = BcoPlugInfo.get_plug_clusters(fcp, addr)
            for cluster in range(len(clusters)):
                clst = BcoPlugInfo.get_plug_cluster_info(fcp, addr, cluster + 1)
                plug['clusters'].append(clst)
        plug['input'] = {}
        plug['outputs'] = []
        # Music subunits have counter direction.
        try:
            plug['input'] = BcoPlugInfo.get_plug_input(fcp, addr)
        except:
            pass
        try:
            plug['outputs'] = BcoPlugInfo.get_plug_outputs(fcp, addr)
        except:
            pass
        return plug

    def _parse_function_block_plugs(self, fcp):
        fbs = {}
        subunits = BcoSubunitInfo.get_subunits(fcp)
        for type in self.subunit_plugs.keys():
            subunit_fbs = {}
            entries = []
            for i in range(0xff):
                try:
                    entries.extend(BcoSubunitInfo.get_subunit_fb_info(fcp,
                                                            type, 0, i, 0xff))
                except:
                    break
            for entry in entries:
                fb_type = entry['fb-type']
                if fb_type not in subunit_fbs:
                    subunit_fbs[fb_type] = []
                subunit_fbs[fb_type].append({'input': [], 'output': []})
            for entry in entries:
                fb_type = entry['fb-type']
                fb_id = entry['fb-id'] - 1
                for i in range(entry['inputs']):
                    plug = self._parse_fb_plug(fcp, 'input', type, 0,
                                               fb_type, fb_id + 1, i)
                    subunit_fbs[fb_type][fb_id]['input'].append(plug)
                for i in range(entry['outputs']):
                    plug = self._parse_fb_plug(fcp, 'output', type, 0,
                                               fb_type, fb_id + 1, i)
                    subunit_fbs[fb_type][fb_id]['output'].append(plug)
            fbs[type] = subunit_fbs
        return fbs

    def _parse_fb_plug(self, fcp, dir, subunit_type, subunit_id, fb_type, fb_id,
                       num):
        plug = {}
        addr = BcoPlugInfo.get_function_block_addr(dir, subunit_type,
                                            subunit_id, fb_type, fb_id, num)
        plug['type'] = BcoPlugInfo.get_plug_type(fcp, addr)
        plug['name'] = BcoPlugInfo.get_plug_name(fcp, addr)
        plug['channels'] = []
        channels = BcoPlugInfo.get_plug_channels(fcp, addr)
        for channel in range(channels):
            ch = BcoPlugInfo.get_plug_ch_name(fcp, addr, channel + 1)
            plug['channels'].append(ch)
        plug['clusters'] = []
        if plug['type'] is 'IsoStream':
            clusters = BcoPlugInfo.get_plug_clusters(fcp, addr)
            for cluster in range(len(clusters)):
                clst = BcoPlugInfo.get_plug_cluster_info(fcp, addr, cluster + 1)
                plug['clusters'].append(clst)
        plug['input'] = {}
        plug['outputs'] = []
        # Music subunits have counter direction.
        try:
            plug['input'] = BcoPlugInfo.get_plug_input(fcp, addr)
        except:
            pass
        try:
            plug['outputs'] = BcoPlugInfo.get_plug_outputs(fcp, addr)
        except:
            pass
        return plug

    def _parse_signal_destination(self, fcp):
        dst = []
        for i, plug in enumerate(self.subunit_plugs['music']['input']):
            if plug['type'] == 'Sync':
                dst = AvcCcm.get_subunit_signal_addr('music', 0, i)
        return dst

    def _parse_signal_sources(self, fcp):
        srcs = {}
        candidates = {}
        # This is internal clock source.
        for i, plug in enumerate(self.subunit_plugs['music']['output']):
           if plug['type'] == 'Sync':
               addr = AvcCcm.get_subunit_signal_addr('music', 0, i)
               candidates[plug['name']] = addr
        # External source is available.
        for i, plug in enumerate(self.unit_plugs['external']['input']):
            if plug['type'] in ('Sync', 'Digital', 'Clock'):
                addr = AvcCcm.get_unit_signal_addr('external', i)
                candidates[plug['name']] = addr
        # SYT-match is available, but not practical.
        for i, plug in enumerate(self.unit_plugs['isoc']['input']):
            if plug['type'] == 'Sync':
                addr = AvcCcm.get_unit_signal_addr('isoc', i)
                candidates[plug['name']] = addr
        # Inquire these are able to connect to destination.
        for key, src in candidates.items():
            try:
                AvcCcm.ask_signal_source(fcp, src, self.signal_destination)
            except:
                continue
            srcs[key] = src
        return srcs

    def _parse_stream_formats(self, fcp):
        hoge = {}
        for type, dir_plugs in self.unit_plugs.items():
            if type == 'async':
                continue
            hoge[type] = {}
            for dir, plugs in dir_plugs.items():
                hoge[type][dir] = []
                for i, plug in enumerate(plugs):
                    addr = BcoPlugInfo.get_unit_addr(dir, type, i)
                    fmts = BcoStreamFormatInfo.get_entry_list(fcp, addr)
                    hoge[type][dir].append(fmts)
        return hoge
