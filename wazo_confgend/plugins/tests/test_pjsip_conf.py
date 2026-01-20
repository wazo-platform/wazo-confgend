# Copyright 2018-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from collections import namedtuple
from io import StringIO
from unittest.mock import patch

from xivo_dao.alchemy.pjsip_transport import PJSIPTransport

from wazo_confgend.generators.tests.util import assert_config_equal

from ..pjsip_conf import PJSIPConfGenerator

SearchResult = namedtuple('SearchResult', ['total', 'items'])


class TestPJSIPConfGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = PJSIPConfGenerator(dependencies=None)

    def test_generate_transports(self):
        output = StringIO()
        with patch('wazo_confgend.plugins.pjsip_conf.transport_dao') as dao:
            dao.search.return_value = SearchResult(
                2,
                [
                    PJSIPTransport(
                        name='transport-udp',
                        options=[
                            ['protocol', 'udp'],
                            ['bind', '0.0.0.0:5060'],
                        ],
                    ),
                    PJSIPTransport(
                        name='transport-wss',
                        options=[
                            ['protocol', 'wss'],
                            ['bind', '0.0.0.0:5060'],
                        ],
                    ),
                ],
            )

            self.generator.generate_transports(output)
            assert_config_equal(
                output.getvalue(),
                '''\
                [transport-udp]
                type = transport
                protocol = udp
                bind = 0.0.0.0:5060

                [transport-wss]
                type = transport
                protocol = wss
                bind = 0.0.0.0:5060
                ''',
            )

    def test_generate_users(self):
        output = StringIO()
        name_1 = 'abcdef'
        label_1 = 'my-sip-line'
        name_2 = 'defbca'
        label_2 = 'another-sip-line'
        with patch('wazo_confgend.plugins.pjsip_conf.asterisk_conf_dao') as dao:
            dao.find_sip_user_settings.return_value = [
                {
                    'name': name_1,
                    'label': label_1,
                    'aor_section_options': [
                        ['type', 'aor'],
                        ['qualify_frequency', '60'],
                    ],
                    'auth_section_options': [
                        ['type', 'auth'],
                        ['username', 'iddqd'],
                    ],
                    'endpoint_section_options': [
                        ['type', 'endpoint'],
                        ['aors', name_1],
                        ['auth', name_1],
                        ['allow', '!all,ulaw'],
                    ],
                },
                {
                    'name': name_2,
                    'label': label_2,
                    'aor_section_options': [
                        ['type', 'aor'],
                        ['qualify_frequency', '42'],
                    ],
                    'auth_section_options': [
                        ['type', 'auth'],
                        ['username', 'idbehold'],
                    ],
                    'endpoint_section_options': [
                        ['type', 'endpoint'],
                        ['aors', name_2],
                        ['auth', name_2],
                        ['allow', '!all,ulaw,g729'],
                    ],
                },
            ]

            self.generator.generate_lines(output)
            result = output.getvalue()
            assert_config_equal(
                result,
                '''\
                ; {label_1}
                [{name_1}]
                type = endpoint
                aors = {name_1}
                auth = {name_1}
                allow = !all,ulaw

                [{name_1}]
                type = aor
                qualify_frequency = 60

                [{name_1}]
                type = auth
                username = iddqd

                ; {label_2}
                [{name_2}]
                type = endpoint
                aors = {name_2}
                auth = {name_2}
                allow = !all,ulaw,g729

                [{name_2}]
                type = aor
                qualify_frequency = 42

                [{name_2}]
                type = auth
                username = idbehold
                '''.format(
                    label_1=label_1,
                    label_2=label_2,
                    name_1=name_1,
                    name_2=name_2,
                ),
            )

    def test_generate_meeting_guests(self):
        output = StringIO()
        name_1 = 'abcdeféèìïöçàäỳÿüùúóíá'
        label_1 = 'meeting_guest_1_uuid'
        name_2 = 'ghijkléèìïöçàäỳÿüùúóíá'
        label_2 = 'meeting_guest_2_uuid'

        with patch('wazo_confgend.plugins.pjsip_conf.asterisk_conf_dao') as dao:
            dao.find_sip_meeting_guests_settings.return_value = [
                {
                    'name': name_1,
                    'label': label_1,
                    'aor_section_options': [
                        ['type', 'aor'],
                        ['qualify_frequency', '60'],
                    ],
                    'auth_section_options': [
                        ['type', 'auth'],
                        ['username', 'iddqd'],
                    ],
                    'endpoint_section_options': [
                        ['type', 'endpoint'],
                        ['aors', name_1],
                        ['auth', name_1],
                        ['allow', '!all,ulaw'],
                    ],
                },
                {
                    'name': name_2,
                    'label': label_2,
                    'aor_section_options': [
                        ['type', 'aor'],
                        ['qualify_frequency', '42'],
                    ],
                    'auth_section_options': [
                        ['type', 'auth'],
                        ['username', 'idbehold'],
                    ],
                    'endpoint_section_options': [
                        ['type', 'endpoint'],
                        ['aors', name_2],
                        ['auth', name_2],
                        ['allow', '!all,ulaw,g729'],
                    ],
                },
            ]

            self.generator.generate_meeting_guests(output)
            result = output.getvalue()
            assert_config_equal(
                result,
                '''\
                ; {label_1}
                [{name_1}]
                type = endpoint
                aors = {name_1}
                auth = {name_1}
                allow = !all,ulaw

                [{name_1}]
                type = aor
                qualify_frequency = 60

                [{name_1}]
                type = auth
                username = iddqd

                ; {label_2}
                [{name_2}]
                type = endpoint
                aors = {name_2}
                auth = {name_2}
                allow = !all,ulaw,g729

                [{name_2}]
                type = aor
                qualify_frequency = 42

                [{name_2}]
                type = auth
                username = idbehold
                '''.format(
                    label_1=label_1,
                    label_2=label_2,
                    name_1=name_1,
                    name_2=name_2,
                ),
            )

    def test_generate_trunks(self):
        output = StringIO()
        name_1 = 'abcdef'
        label_1 = 'my-sip-trunk'
        with patch('wazo_confgend.plugins.pjsip_conf.asterisk_conf_dao') as dao:
            dao.find_sip_trunk_settings.return_value = [
                {
                    'name': name_1,
                    'label': label_1,
                    'aor_section_options': [
                        ['type', 'aor'],
                        ['qualify_frequency', '60'],
                    ],
                    'auth_section_options': [
                        ['type', 'auth'],
                        ['username', 'iddqd'],
                    ],
                    'endpoint_section_options': [
                        ['type', 'endpoint'],
                        ['aors', name_1],
                        ['auth', name_1],
                        ['allow', '!all,ulaw'],
                        ['outbound_auth', f'outbound_auth_{name_1}'],
                    ],
                    'identify_section_options': [
                        ['type', 'identify'],
                        ['match', '54.172.60.0'],
                        ['match', '54.172.60.1'],
                        ['endpoint', name_1],
                    ],
                    'registration_section_options': [
                        ['type', 'registration'],
                        ['expiration', '120'],
                        [
                            'outbound_auth',
                            'auth_reg_dev_370@gateway.example.com',
                        ],
                    ],
                    'registration_outbound_auth_section_options': [
                        ['type', 'auth'],
                        ['username', 'reg_username'],
                        ['password', 'secret'],
                    ],
                    'outbound_auth_section_options': [
                        ['type', 'auth'],
                        ['username', 'outbound_auth_username'],
                        ['password', 'secret'],
                    ],
                },
            ]

            self.generator.generate_trunks(output)
            result = output.getvalue()
            assert_config_equal(
                result,
                '''\
                ; {label_1}
                [{name_1}]
                type = endpoint
                aors = {name_1}
                auth = {name_1}
                allow = !all,ulaw
                outbound_auth = outbound_auth_{name_1}

                [{name_1}]
                type = aor
                qualify_frequency = 60

                [{name_1}]
                type = auth
                username = iddqd

                [{name_1}]
                type = identify
                match = 54.172.60.0
                match = 54.172.60.1
                endpoint = {name_1}

                [outbound_auth_{name_1}]
                type = auth
                username = outbound_auth_username
                password = secret

                [auth_reg_dev_370@gateway.example.com]
                type = auth
                username = reg_username
                password = secret

                [{name_1}]
                type = registration
                expiration = 120
                outbound_auth = auth_reg_dev_370@gateway.example.com
                '''.format(
                    label_1=label_1, name_1=name_1
                ),
            )
