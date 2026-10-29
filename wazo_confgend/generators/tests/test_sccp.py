# Copyright 2011-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


import io
import itertools
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from wazo_confgend.generators.sccp import (
    ABSOLUTE_CHANNEL_TIMEOUT,
    SccpConf,
    _SccpDeviceConf,
    _SccpGeneralSettingsConf,
    _SccpLineConf,
    _SccpSpeedDialConf,
    _SplittedGeneralSettings,
)
from wazo_confgend.generators.tests.util import (
    assert_config_equal,
    assert_generates_config,
)
from wazo_confgend.generators.util import AsteriskFileWriter


class TestSccpConf(unittest.TestCase):
    @patch(
        'xivo_dao.asterisk_conf_dao.find_sccp_general_settings', Mock(return_value=[])
    )
    @patch('xivo_dao.asterisk_conf_dao.find_sccp_line_settings', Mock(return_value=[]))
    @patch(
        'xivo_dao.asterisk_conf_dao.find_sccp_device_settings', Mock(return_value=[])
    )
    @patch(
        'xivo_dao.asterisk_conf_dao.find_sccp_speeddial_settings', Mock(return_value=[])
    )
    def setUp(self):
        self._output = io.StringIO()
        self._conf = SccpConf()

    def test_generate(self):
        assert_generates_config(
            self._conf,
            f'''
            [general]

            [xivo_device_tpl](!)

            [guest](xivo_device_tpl)
            type = device
            line = guestline

            [xivo_line_tpl](!)
            setvar = TIMEOUT(absolute)={ABSOLUTE_CHANNEL_TIMEOUT}

            [guestline](xivo_line_tpl)
            type = line
            context = xivo-initconfig
            cid_name = Autoprov
            cid_num = autoprov
        ''',
        )

    def test_one_element_speeddials_section(self):
        speedials = [
            {
                'exten': '1001',
                'fknum': 1,
                'label': 'user001',
                'supervision': 0,
                'user_id': 1229,
                'device': 'SEPACA016FDF235',
            }
        ]

        sccp_conf = _SccpSpeedDialConf()
        sccp_conf.generate(speedials, self._output)

        assert_config_equal(
            self._output.getvalue(),
            '''
            [1229-1]
            type = speeddial
            extension = 1001
            label = user001
            blf = 0
        ''',
        )

    def test_speeddial_no_label(self):
        speedials = [
            {
                'exten': '1001',
                'fknum': 1,
                'label': None,
                'supervision': 0,
                'user_id': 1229,
                'device': 'SEPACA016FDF235',
            }
        ]

        sccp_conf = _SccpSpeedDialConf()
        sccp_conf.generate(speedials, self._output)

        assert_config_equal(
            self._output.getvalue(),
            '''
            [1229-1]
            type = speeddial
            extension = 1001
            blf = 0
        ''',
        )


class TestSccpGeneralConf(unittest.TestCase):
    def setUp(self):
        self._general_conf = _SccpGeneralSettingsConf()
        self._output = io.StringIO()

    def test_one_element_general_section(self):
        items = [{'option_name': 'foo', 'option_value': 'bar'}]

        self._general_conf.generate(items, self._output)

        assert_config_equal(
            self._output.getvalue(),
            '''
            [general]
            foo = bar
        ''',
        )


class TestSccpSplittedGeneralSettings(unittest.TestCase):
    def test_split_options(self):
        general_items = [
            {'option_name': 'foo'},
        ]
        device_items = [
            {'option_name': 'keepalive'},
        ]
        line_items = [
            {'option_name': 'language'},
        ]
        items = list(itertools.chain(general_items, device_items, line_items))

        splitted_settings = _SplittedGeneralSettings.new_from_dao_general_settings(
            items
        )

        self.assertEqual(general_items, splitted_settings.general_items)
        self.assertEqual(device_items, splitted_settings.device_items)
        self.assertEqual(line_items, splitted_settings.line_items)


class TestSccpDeviceConf(unittest.TestCase):
    def setUp(self):
        self._device_conf = _SccpDeviceConf([])
        self._output = io.StringIO()
        self._ast_writer = AsteriskFileWriter(self._output)

    def test_template_items(self):
        items = [
            {'option_name': 'foo', 'option_value': 'bar'},
        ]

        self._device_conf._generate_template(items, self._ast_writer)

        assert_config_equal(
            self._output.getvalue(),
            '''
            [xivo_device_tpl](!)
            foo = bar
        ''',
        )

    def test_one_device_no_line_no_voicemail(self):
        sccpdevice = [
            {
                'category': 'devices',
                'name': 'SEPACA016FDF235',
                'device': 'SEPACA016FDF235',
                'line': '',
                'voicemail': '',
            }
        ]

        self._device_conf._generate_devices(sccpdevice, self._ast_writer)

        assert_config_equal(
            self._output.getvalue(),
            '''
            [SEPACA016FDF235](xivo_device_tpl)
            type = device
        ''',
        )

    def test_one_element_devices_section(self):
        sccpdevice = [
            {
                'category': 'devices',
                'name': 'SEPACA016FDF235',
                'device': 'SEPACA016FDF235',
                'line': '103',
                'voicemail': '103',
            }
        ]

        sccpspeeddials = [
            {
                'exten': '1001',
                'fknum': 1,
                'label': 'user001',
                'supervision': 0,
                'user_id': 1229,
                'device': 'SEPACA016FDF235',
            }
        ]

        device_conf = _SccpDeviceConf(sccpspeeddials)
        device_conf._generate_devices(sccpdevice, self._ast_writer)

        assert_config_equal(
            self._output.getvalue(),
            '''
            [SEPACA016FDF235](xivo_device_tpl)
            type = device
            line = 103
            voicemail = 103
            speeddial = 1229-1
        ''',
        )

    def test_multiple_speedials_devices_section(self):
        sccpdevice = [
            {
                'category': 'devices',
                'name': 'SEPACA016FDF235',
                'device': 'SEPACA016FDF235',
                'line': '103',
                'voicemail': '103',
            }
        ]

        sccpspeeddials = [
            {
                'exten': '1002',
                'fknum': 2,
                'label': 'user002',
                'supervision': 0,
                'user_id': 1229,
                'device': 'SEPACA016FDF235',
            },
            {
                'exten': '1001',
                'fknum': 1,
                'label': 'user001',
                'supervision': 0,
                'user_id': 1229,
                'device': 'SEPACA016FDF235',
            },
        ]

        device_conf = _SccpDeviceConf(sccpspeeddials)
        device_conf._generate_devices(sccpdevice, self._ast_writer)

        assert_config_equal(
            self._output.getvalue(),
            '''
            [SEPACA016FDF235](xivo_device_tpl)
            type = device
            line = 103
            voicemail = 103
            speeddial = 1229-1
            speeddial = 1229-2
        ''',
        )


class TestSccpLineConf(unittest.TestCase):
    def setUp(self):
        self._line_conf = _SccpLineConf()
        self._output = io.StringIO()
        self._ast_writer = AsteriskFileWriter(self._output)

    def test_template_directmedia_option(self):
        items = [
            {'option_name': 'directmedia', 'option_value': 'no'},
        ]

        self._line_conf._generate_template(items, self._ast_writer)

        assert_config_equal(
            self._output.getvalue(),
            f'''
            [xivo_line_tpl](!)
            directmedia = 0
            setvar = TIMEOUT(absolute)={ABSOLUTE_CHANNEL_TIMEOUT}
        ''',
        )

    def test_template_allow_option(self):
        items = [
            {'option_name': 'allow', 'option_value': 'ulaw'},
        ]

        self._line_conf._generate_template(items, self._ast_writer)

        assert_config_equal(
            self._output.getvalue(),
            f'''
            [xivo_line_tpl](!)
            disallow = all
            allow = ulaw
            setvar = TIMEOUT(absolute)={ABSOLUTE_CHANNEL_TIMEOUT}

        ''',
        )

    def test_template_empty_allow_option(self):
        items = [
            {'option_name': 'allow', 'option_value': ''},
        ]

        self._line_conf._generate_template(items, self._ast_writer)

        assert_config_equal(
            self._output.getvalue(),
            f'''
            [xivo_line_tpl](!)
            setvar = TIMEOUT(absolute)={ABSOLUTE_CHANNEL_TIMEOUT}
        ''',
        )

    def test_template_disallow_option_is_ignored(self):
        items = [
            {'option_name': 'disallow', 'option_value': 'foobar'},
        ]

        self._line_conf._generate_template(items, self._ast_writer)

        assert_config_equal(
            self._output.getvalue(),
            f'''
            [xivo_line_tpl](!)
            setvar = TIMEOUT(absolute)={ABSOLUTE_CHANNEL_TIMEOUT}
        ''',
        )

    def test_one_element_lines_section(self):
        uuid = str(uuid4())
        sccpline = [
            {
                'id': 13423,
                'category': 'lines',
                'name': '100',
                'cid_name': 'jimmy',
                'cid_num': '100',
                'user_id': '1',
                'uuid': uuid,
                'language': 'fr_FR',
                'number': '100',
                'context': 'a_context',
                'tenant_uuid': 'tenant-uuid',
                'enable_online_recording': 1,
                'simultcalls': 5,
            }
        ]

        self._line_conf._generate_lines(sccpline, self._ast_writer)

        assert_config_equal(
            self._output.getvalue(),
            f'''
            [100](xivo_line_tpl)
            type = line
            cid_name = jimmy
            cid_num = 100
            setvar = XIVO_ORIGINAL_CALLER_ID="jimmy" <100>
            setvar = XIVO_USERID=1
            setvar = WAZO_USERID=1
            setvar = XIVO_USERUUID={uuid}
            setvar = WAZO_USERUUID={uuid}
            setvar = WAZO_TENANT_UUID=tenant-uuid
            setvar = PICKUPMARK=100%a_context
            setvar = TRANSFER_CONTEXT=a_context
            setvar = WAZO_CHANNEL_DIRECTION=from-wazo
            setvar = WAZO_LINE_ID=13423
            setvar = WAZO_CALLER_SIMULTCALLS=5
            setvar = CHANNEL(hangup_handler_push)=wazo-stamp-cel-participant,s,1({uuid},tenant-uuid,13423)
            setvar = DYNAMIC_FEATURES=togglerecord
            language = fr_FR
            context = a_context
        ''',
        )

    def test_one_element_lines_section_no_language(self):
        uuid = str(uuid4())
        sccpline = [
            {
                'id': 13423,
                'category': 'lines',
                'name': '100',
                'cid_name': 'jimmy',
                'cid_num': '100',
                'user_id': '1',
                'uuid': uuid,
                'language': None,
                'number': '100',
                'context': 'a_context',
                'tenant_uuid': 'tenant-uuid',
                'enable_online_recording': 0,
                'simultcalls': 5,
            }
        ]

        self._line_conf._generate_lines(sccpline, self._ast_writer)

        assert_config_equal(
            self._output.getvalue(),
            f'''
            [100](xivo_line_tpl)
            type = line
            cid_name = jimmy
            cid_num = 100
            setvar = XIVO_ORIGINAL_CALLER_ID="jimmy" <100>
            setvar = XIVO_USERID=1
            setvar = WAZO_USERID=1
            setvar = XIVO_USERUUID={uuid}
            setvar = WAZO_USERUUID={uuid}
            setvar = WAZO_TENANT_UUID=tenant-uuid
            setvar = PICKUPMARK=100%a_context
            setvar = TRANSFER_CONTEXT=a_context
            setvar = WAZO_CHANNEL_DIRECTION=from-wazo
            setvar = WAZO_LINE_ID=13423
            setvar = WAZO_CALLER_SIMULTCALLS=5
            setvar = CHANNEL(hangup_handler_push)=wazo-stamp-cel-participant,s,1({uuid},tenant-uuid,13423)
            context = a_context
        ''',
        )

    def test_allow_no_disallow(self):
        uuid = str(uuid4())
        sccpline = [
            {
                'id': 13423,
                'category': 'lines',
                'name': '100',
                'cid_name': 'jimmy',
                'cid_num': '100',
                'user_id': '1',
                'language': None,
                'number': '100',
                'context': 'a_context',
                'allow': 'g729,ulaw',
                'uuid': uuid,
                'tenant_uuid': 'tenant-uuid',
                'enable_online_recording': 0,
                'simultcalls': 5,
            }
        ]

        self._line_conf._generate_lines(sccpline, self._ast_writer)

        assert_config_equal(
            self._output.getvalue(),
            f'''
            [100](xivo_line_tpl)
            type = line
            cid_name = jimmy
            cid_num = 100
            setvar = XIVO_ORIGINAL_CALLER_ID="jimmy" <100>
            setvar = XIVO_USERID=1
            setvar = WAZO_USERID=1
            setvar = XIVO_USERUUID={uuid}
            setvar = WAZO_USERUUID={uuid}
            setvar = WAZO_TENANT_UUID=tenant-uuid
            setvar = PICKUPMARK=100%a_context
            setvar = TRANSFER_CONTEXT=a_context
            setvar = WAZO_CHANNEL_DIRECTION=from-wazo
            setvar = WAZO_LINE_ID=13423
            setvar = WAZO_CALLER_SIMULTCALLS=5
            setvar = CHANNEL(hangup_handler_push)=wazo-stamp-cel-participant,s,1({uuid},tenant-uuid,13423)
            context = a_context
            allow = g729,ulaw
        ''',
        )

    def test_disallow_all_allow_order(self):
        uuid = str(uuid4())
        sccpline = [
            {
                'id': 13423,
                'category': 'lines',
                'name': '100',
                'cid_name': 'jimmy',
                'cid_num': '100',
                'user_id': '1',
                'uuid': uuid,
                'language': None,
                'number': '100',
                'context': 'a_context',
                'allow': 'g729,ulaw',
                'disallow': 'all',
                'tenant_uuid': 'tenant-uuid',
                'enable_online_recording': 0,
                'simultcalls': 5,
            }
        ]

        self._line_conf._generate_lines(sccpline, self._ast_writer)

        assert_config_equal(
            self._output.getvalue(),
            f'''
            [100](xivo_line_tpl)
            type = line
            cid_name = jimmy
            cid_num = 100
            setvar = XIVO_ORIGINAL_CALLER_ID="jimmy" <100>
            setvar = XIVO_USERID=1
            setvar = WAZO_USERID=1
            setvar = XIVO_USERUUID={uuid}
            setvar = WAZO_USERUUID={uuid}
            setvar = WAZO_TENANT_UUID=tenant-uuid
            setvar = PICKUPMARK=100%a_context
            setvar = TRANSFER_CONTEXT=a_context
            setvar = WAZO_CHANNEL_DIRECTION=from-wazo
            setvar = WAZO_LINE_ID=13423
            setvar = WAZO_CALLER_SIMULTCALLS=5
            setvar = CHANNEL(hangup_handler_push)=wazo-stamp-cel-participant,s,1({uuid},tenant-uuid,13423)
            context = a_context
            disallow = all
            allow = g729,ulaw
        ''',
        )

    def test_call_and_pickup_groups(self):
        uuid = str(uuid4())
        sccpline = [
            {
                'id': 13423,
                'category': 'lines',
                'name': '100',
                'cid_name': 'jimmy',
                'cid_num': '100',
                'user_id': '1',
                'uuid': uuid,
                'language': None,
                'number': '100',
                'context': 'a_context',
                'callgroup': [1, 2, 3, 4],
                'pickupgroup': [3, 4],
                'tenant_uuid': 'tenant-uuid',
                'enable_online_recording': 0,
                'simultcalls': 5,
            }
        ]

        self._line_conf._generate_lines(sccpline, self._ast_writer)

        assert_config_equal(
            self._output.getvalue(),
            f'''
            [100](xivo_line_tpl)
            type = line
            cid_name = jimmy
            cid_num = 100
            setvar = XIVO_ORIGINAL_CALLER_ID="jimmy" <100>
            setvar = XIVO_USERID=1
            setvar = WAZO_USERID=1
            setvar = XIVO_USERUUID={uuid}
            setvar = WAZO_USERUUID={uuid}
            setvar = WAZO_TENANT_UUID=tenant-uuid
            setvar = PICKUPMARK=100%a_context
            setvar = TRANSFER_CONTEXT=a_context
            setvar = WAZO_CHANNEL_DIRECTION=from-wazo
            setvar = WAZO_LINE_ID=13423
            setvar = WAZO_CALLER_SIMULTCALLS=5
            setvar = CHANNEL(hangup_handler_push)=wazo-stamp-cel-participant,s,1({uuid},tenant-uuid,13423)
            context = a_context
            namedcallgroup = 1,2,3,4
            namedpickupgroup = 3,4
        ''',
        )
