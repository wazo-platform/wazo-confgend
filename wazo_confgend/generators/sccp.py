# Copyright 2011-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


from operator import itemgetter

from xivo_dao import asterisk_conf_dao

from wazo_confgend.generators.util import AsteriskFileWriter

_GUEST_DEVICE_NAME = 'guest'
_GUEST_LINE_NAME = 'guestline'
# absolute timeout in seconds, limiting max call duration
ABSOLUTE_CHANNEL_TIMEOUT = '36000'


class SccpConf:
    def __init__(self):
        self._sccpgeneralsettings = asterisk_conf_dao.find_sccp_general_settings()
        self._sccpline = asterisk_conf_dao.find_sccp_line_settings()
        self._sccpdevice = asterisk_conf_dao.find_sccp_device_settings()
        self._sccpspeeddial = asterisk_conf_dao.find_sccp_speeddial_settings()

    def generate(self, output):
        splitted_settings = _SplittedGeneralSettings.new_from_dao_general_settings(
            self._sccpgeneralsettings
        )

        sccp_general_conf = _SccpGeneralSettingsConf()
        sccp_general_conf.generate(splitted_settings.general_items, output)

        sccp_device_conf = _SccpDeviceConf(self._sccpspeeddial)
        sccp_device_conf.generate(
            self._sccpdevice, splitted_settings.device_items, output
        )

        sccp_line_conf = _SccpLineConf()
        sccp_line_conf.generate(self._sccpline, splitted_settings.line_items, output)

        sccp_speeddial_conf = _SccpSpeedDialConf()
        sccp_speeddial_conf.generate(self._sccpspeeddial, output)


class _SplittedGeneralSettings:
    _DEVICE_OPTIONS = ['dialtimeout', 'dateformat', 'vmexten', 'keepalive']
    _LINES_OPTIONS = [
        'context',
        'language',
        'directmedia',
        'tos_audio',
        'disallow',
        'allow',
    ]

    def __init__(self, general_items, device_items, line_items):
        self.general_items = general_items
        self.device_items = device_items
        self.line_items = line_items

    @classmethod
    def new_from_dao_general_settings(cls, sccp_general_settings):
        general_items = []
        device_items = []
        line_items = []

        for item in sccp_general_settings:
            option_name = item['option_name']
            if option_name in cls._DEVICE_OPTIONS:
                device_items.append(item)
            elif option_name in cls._LINES_OPTIONS:
                line_items.append(item)
            else:
                general_items.append(item)

        return cls(general_items, device_items, line_items)


class _SccpGeneralSettingsConf:
    def generate(self, general_items, output):
        ast_writer = AsteriskFileWriter(output)
        ast_writer.write_section('general')
        for item in general_items:
            ast_writer.write_option(item['option_name'], item['option_value'])
        ast_writer.write_newline()


class _SccpDeviceConf:
    _TPL_NAME = 'xivo_device_tpl'

    def __init__(self, sccpspeeddialdevices):
        self._sccpspeeddialdevices = sorted(
            sccpspeeddialdevices,
            key=itemgetter('fknum'),
        )

    def generate(self, sccpdevice, general_device_items, output):
        ast_writer = AsteriskFileWriter(output)
        self._generate_template(general_device_items, ast_writer)
        self._generate_guest_device(ast_writer)
        self._generate_devices(sccpdevice, ast_writer)

    def _generate_template(self, device_items, ast_writer):
        ast_writer.write_section_tpl(self._TPL_NAME)
        for item in device_items:
            ast_writer.write_option(item['option_name'], item['option_value'])
        ast_writer.write_newline()

    def _generate_guest_device(self, ast_writer):
        ast_writer.write_section_using_tpl(_GUEST_DEVICE_NAME, self._TPL_NAME)
        ast_writer.write_option('type', 'device')
        ast_writer.write_option('line', _GUEST_LINE_NAME)
        ast_writer.write_newline()

    def _generate_devices(self, sccpdevice, ast_writer):
        for item in sccpdevice:
            ast_writer.write_section_using_tpl(item['name'], self._TPL_NAME)
            ast_writer.write_option('type', 'device')
            if item['line']:
                ast_writer.write_option('line', item['line'])
            if item['voicemail']:
                ast_writer.write_option('voicemail', item['voicemail'])
            self._generate_speeddials(item['device'], ast_writer)
            ast_writer.write_newline()

    def _generate_speeddials(self, device, ast_writer):
        for item in self._sccpspeeddialdevices:
            if item['device'] == device:
                ast_writer.write_option(
                    'speeddial', f"{item['user_id']:d}-{item['fknum']:d}"
                )


class _SccpLineConf:
    _TPL_NAME = 'xivo_line_tpl'

    def generate(self, sccplines, general_line_items, output):
        ast_writer = AsteriskFileWriter(output)
        self._generate_template(general_line_items, ast_writer)
        self._generate_guest_line(ast_writer)
        self._generate_lines(sccplines, ast_writer)

    def _generate_template(self, line_items, ast_writer):
        ast_writer.write_section_tpl(self._TPL_NAME)
        for item in line_items:
            option_name = item['option_name']
            option_value = item['option_value']

            if option_name == 'allow':
                if not option_value:
                    continue
                ast_writer.write_option('disallow', 'all')
            elif option_name == 'disallow':
                continue
            elif option_name == 'directmedia':
                option_value = '0' if option_value == 'no' else '1'
            ast_writer.write_option(option_name, option_value)
        ast_writer.write_option(
            'setvar', f'TIMEOUT(absolute)={ABSOLUTE_CHANNEL_TIMEOUT}'
        )
        ast_writer.write_newline()

    def _generate_guest_line(self, ast_writer):
        ast_writer.write_section_using_tpl(_GUEST_LINE_NAME, self._TPL_NAME)
        ast_writer.write_option('type', 'line')
        ast_writer.write_option('context', 'xivo-initconfig')
        ast_writer.write_option('cid_name', 'Autoprov')
        ast_writer.write_option('cid_num', 'autoprov')
        ast_writer.write_newline()

    def _generate_lines(self, sccplines, ast_writer):
        for item in sccplines:
            ast_writer.write_section_using_tpl(item['name'], self._TPL_NAME)
            ast_writer.write_option('type', 'line')
            ast_writer.write_option('cid_name', item['cid_name'])
            ast_writer.write_option('cid_num', item['cid_num'])
            ast_writer.write_option(
                'setvar',
                'XIVO_ORIGINAL_CALLER_ID="{cid_name}" <{cid_num}>'.format(**item),
            )
            ast_writer.write_option(
                'setvar', f"XIVO_USERID={item['user_id']}"
            )  # Deprecated in 24.01
            ast_writer.write_option('setvar', f"WAZO_USERID={item['user_id']}")
            ast_writer.write_option(
                'setvar', f"XIVO_USERUUID={item['uuid']}"
            )  # Deprecated in 24.01
            ast_writer.write_option('setvar', f"WAZO_USERUUID={item['uuid']}")
            ast_writer.write_option('setvar', f"WAZO_TENANT_UUID={item['tenant_uuid']}")
            ast_writer.write_option(
                'setvar', 'PICKUPMARK={number}%{context}'.format(**item)
            )
            ast_writer.write_option('setvar', f"TRANSFER_CONTEXT={item['context']}")
            ast_writer.write_option('setvar', 'WAZO_CHANNEL_DIRECTION=from-wazo')
            ast_writer.write_option('setvar', f"WAZO_LINE_ID={item['id']}")
            ast_writer.write_option(
                'setvar', f"WAZO_CALLER_SIMULTCALLS={item['simultcalls']}"
            )
            ast_writer.write_option(
                'setvar',
                'CHANNEL(hangup_handler_push)=wazo-stamp-cel-participant,s,1'
                f"({item['uuid']},{item['tenant_uuid']},{item['id']})",
            )

            if item['enable_online_recording']:
                ast_writer.write_option('setvar', 'DYNAMIC_FEATURES=togglerecord')
            if item['language']:
                ast_writer.write_option('language', item['language'])
            ast_writer.write_option('context', item['context'])
            if 'disallow' in item:
                ast_writer.write_option('disallow', item['disallow'])
            if 'allow' in item:
                ast_writer.write_option('allow', item['allow'])
            if 'callgroup' in item:
                ast_writer.write_option(
                    'namedcallgroup', ','.join(map(str, item['callgroup']))
                )
            if 'pickupgroup' in item:
                ast_writer.write_option(
                    'namedpickupgroup', ','.join(map(str, item['pickupgroup']))
                )
            ast_writer.write_newline()


class _SccpSpeedDialConf:
    def generate(self, sccpspeeddial, output):
        ast_writer = AsteriskFileWriter(output)
        for item in sccpspeeddial:
            ast_writer.write_section(f"{item['user_id']:d}-{item['fknum']:d}")
            ast_writer.write_option('type', 'speeddial')
            ast_writer.write_option('extension', item['exten'])
            if item['label']:
                ast_writer.write_option('label', item['label'])
            ast_writer.write_option('blf', item['supervision'])
            ast_writer.write_newline()
