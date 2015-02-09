# -*- coding: utf-8 -*-

# Copyright (C) 2011-2014 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import unittest
from StringIO import StringIO

from xivo_confgen.generators import sip


class TestSipConf(unittest.TestCase):

    def setUp(self):
        self.sip_conf = sip.SipConf()

    def tearDown(self):
        pass

    def test_get_line(self):
        result = sip.gen_value_line('emailbody', 'pépè')
        self.assertEqual(result, u'emailbody = pépè')

    def test_unicodify_string(self):
        self.assertEqual(u'pépé', sip.unicodify_string(u'pépé'))
        self.assertEqual(u'pépé', sip.unicodify_string(u'pépé'.encode('utf8')))
        self.assertEqual(u'pépé', sip.unicodify_string('pépé'))
        self.assertEqual(u'8', sip.unicodify_string(8))

    def test_gen_general(self):
        staticsip = [
            {'filename': u'sip.conf', 'category': u'general', 'var_name': u'autocreate_prefix', 'var_val': u'apv6Ym3fJW'},
            {'filename': u'sip.conf', 'category': u'general', 'var_name': u'language', 'var_val': u'fr_FR'},
            {'filename': u'sip.conf', 'category': u'general', 'var_name': u'jbtargetextra', 'var_val': None},
            {'filename': u'sip.conf', 'category': u'general', 'var_name': u'notifycid', 'var_val': u'no'},
            {'filename': u'sip.conf', 'category': u'general', 'var_name': u'session-expires', 'var_val': u'600'},
            {'filename': u'sip.conf', 'category': u'general', 'var_name': u'vmexten', 'var_val': u'*98'},
        ]
        output = StringIO()
        self.sip_conf._gen_general(staticsip, output)
        result = output.getvalue()
        self.assertTrue(u'[general]' in result)
        self.assertTrue(u'autocreate_prefix = apv6Ym3fJW' in result)
        self.assertTrue(u'language = fr_FR' in result)
        self.assertTrue(u'notifycid = no' in result)
        self.assertTrue(u'session-expires = 600' in result)
        self.assertTrue(u'vmexten = *98' in result)

    def test_gen_authentication(self):
        sipauthentication = [{'id': 1, 'usersip_id': None, 'user': u'test', 'secretmode': u'md5',
                              'secret': u'test', 'realm': u'test.com'}]
        output = StringIO()
        self.sip_conf._gen_authentication(sipauthentication, output)
        result = output.getvalue()
        self.assertTrue(u'[authentication]' in result)
        self.assertTrue(u'auth = test#test@test.com' in result)

    def test_gen_authentication_empty(self):
        sipauthentication = []
        output = StringIO()
        self.sip_conf._gen_authentication(sipauthentication, output)
        result = output.getvalue()
        self.assertEqual(u'', result)

    def test_gen_trunk(self):
        trunksip = [{'id': 10, 'name': u'cedric_51', 'type': u'peer', 'username': u'cedric_51',
                    'secret': u'cedric_51', 'md5secret': u'', 'context': u'default', 'language': None,
                    'accountcode': None, 'amaflags': u'default', 'allowtransfer': None, 'fromuser': None,
                    'fromdomain': None, 'mailbox': None, 'subscribemwi': 0, 'buggymwi': None, 'call-limit': 0,
                    'callerid': None, 'fullname': None, 'cid_number': None, 'maxcallbitrate': None,
                    'insecure': None, 'nat': None, 'promiscredir': None, 'usereqphone': None,
                    'videosupport': None, 'trustrpid': None, 'sendrpid': None, 'allowsubscribe': None,
                    'allowoverlap': None, 'dtmfmode': None, 'rfc2833compensate': None, 'qualify': None,
                    'g726nonstandard': None, 'disallow': None, 'allow': None, 'autoframing': None,
                    'mohinterpret': None, 'mohsuggest': None, 'useclientcode': None, 'progressinband': None,
                    't38pt_udptl': None, 't38pt_usertpsource': None, 'rtptimeout': None, 'rtpholdtimeout': None,
                    'rtpkeepalive': None, 'deny': None, 'permit': None, 'defaultip': None, 'setvar': u'',
                    'host': u'dynamic', 'port': 5060, 'regexten': None, 'subscribecontext': None,
                    'fullcontact': None, 'vmexten': None, 'callingpres': None, 'ipaddr': u'', 'regseconds': 0,
                    'regserver': None, 'lastms': u'', 'parkinglot': None, 'protocol': u'sip', 'category': u'trunk',
                    'outboundproxy': None, 'transport': u'udp', 'remotesecret': None, 'directmedia': u'yes',
                    'callcounter': None, 'busylevel': None, 'ignoresdpversion': None, 'session-timers': None,
                    'session-expires': None, 'session-minse': None, 'session-refresher': None,
                    'callbackextension': None, 'registertrying': None, 'timert1': None, 'timerb': None,
                    'qualifyfreq': None, 'contactpermit': None, 'contactdeny': None, 'unsolicited_mailbox': None,
                    'use_q850_reason': None, 'encryption': None, 'snom_aoc_enabled': None, 'maxforwards': None,
                    'disallowed_methods': None, 'textsupport': None, 'callgroup': None, 'pickupgroup': None,
                    'commented': 0}]
        output = StringIO()
        self.sip_conf._gen_trunk(trunksip, output)
        result = output.getvalue()
        self.assertTrue(u'[cedric_51]' in result)
        self.assertTrue(u'amaflags = default' in result)
        self.assertTrue(u'call-limit = 0' in result)
        self.assertTrue(u'context = default' in result)
        self.assertTrue(u'directmedia = yes' in result)
        self.assertTrue(u'host = dynamic' in result)
        self.assertTrue(u'port = 5060' in result)
        self.assertTrue(u'regseconds = 0' in result)
        self.assertTrue(u'secret = cedric_51' in result)
        self.assertTrue(u'subscribemwi = 0' in result)
        self.assertTrue(u'transport = udp' in result)
        self.assertTrue(u'type = peer' in result)
        self.assertTrue(u'username = cedric_51' in result)

    def test__gen_user(self):
        pickup = []
        ccss_options = {
            'cc_foobar': 'foo',
        }
        user = [{'name': 'jean-yves',
                'amaflags': 'default',
                'callerid': '"lucky" <45789>',
                'call-limit': 10,
                'number': 101,
                'context': 'default'}]
        output = StringIO()
        self.sip_conf._gen_user(pickup, user, ccss_options, output)
        result = output.getvalue()
        self.assertIn(u'[jean-yves]', result)
        self.assertIn(u'amaflags = default', result)
        self.assertIn(u'call-limit = 10', result)
        self.assertIn(u'callerid = "lucky" <45789>', result)
        self.assertIn(u'cc_foobar = foo', result)

    def test__gen_user_with_accent(self):
        pickup = []
        ccss_options = {}
        user = [{'name': 'papi',
                'callerid': '"pépè" <45789>',
                'number': 101,
                'context': 'default'}]
        output = StringIO()

        self.sip_conf._gen_user(pickup, user, ccss_options, output)

        self.assertIn(u'callerid = "pépè" <45789>', output.getvalue())

    def test__gen_user_empty_value(self):
        pickup = []
        ccss_options = {}
        user = [{'name': 'novalue',
                 'foobar': '',
                 'number': 101,
                 'context': 'default'}]
        output = StringIO()

        self.sip_conf._gen_user(pickup, user, ccss_options, output)

        self.assertNotIn(u'foobar', output.getvalue())

        user = [{'name': 'novalue',
                 'foobar': None,
                 'number': 101,
                 'context': 'default'}]
        output = StringIO()

        self.sip_conf._gen_user(pickup, user, ccss_options, output)

        self.assertNotIn(u'foobar', output.getvalue())

    def test__gen_user_codec(self):
        pickup = []
        ccss_options = {}
        user = [{'name': 'papi',
                'allow': 'g723,gsm',
                'number': 101,
                'context': 'default'}]
        output = StringIO()

        self.sip_conf._gen_user(pickup, user, ccss_options, output)

        result = output.getvalue()
        self.assertIn('disallow = all', result)
        self.assertIn('allow = g723', result)
        self.assertIn('allow = gsm', result)

    def test__gen_user_subscribemwi(self):
        pickup = []
        ccss_options = {}
        user = [{'name': 'voicemail',
                'subscribemwi': 0,
                'number': 101,
                'context': 'default'}]
        output = StringIO()

        self.sip_conf._gen_user(pickup, user, ccss_options, output)

        self.assertIn('subscribemwi = no', output.getvalue())

        user = [{'name': 'voicemail',
                'subscribemwi': 1,
                'number': 101,
                'context': 'default'}]
        output = StringIO()

        self.sip_conf._gen_user(pickup, user, ccss_options, output)

        self.assertIn('subscribemwi = yes', output.getvalue())

    def test__gen_user_unused_keys(self):
        pickup = []
        ccss_options = {}
        user = [{'id': 1,
                'name': 'unused',
                'protocol': 'sip',
                'category': 5,
                'commented': 0,
                'initialized': 1,
                'disallow': 'all',
                'regseconds': 1,
                'lastms': 5,
                'fullcontact': 'pepe',
                'ipaddr': None,
                'number': 101,
                'context': 'default'}]
        output = StringIO()

        self.sip_conf._gen_user(pickup, user, ccss_options, output)

        result = output.getvalue()
        self.assertNotIn('id', result)
        self.assertNotIn('protocol', result)
        self.assertNotIn('category', result)
        self.assertNotIn('commented', result)
        self.assertNotIn('initialized', result)
        self.assertNotIn('disallow', result)
        self.assertNotIn('regseconds', result)
        self.assertNotIn('lastms', result)
        self.assertNotIn('fullcontact', result)
        self.assertNotIn('ipaddr', result)
        self.assertNotIn('number', result)

    def test__gen_user_transfer_context(self):
        pickup = []
        ccss_options = {}
        user = [{'name': 'othercontext',
                 'number': 101,
                 'context': 'mycontext'}]
        output = StringIO()

        self.sip_conf._gen_user(pickup, user, ccss_options, output)

        self.assertIn('setvar = TRANSFER_CONTEXT=mycontext', output.getvalue())

    def test__gen_user_pickupmark(self):
        pickup = []
        ccss_options = {}
        user = [{'name': 'othercontext',
                 'number': 101,
                 'context': 'mycontext'}]
        output = StringIO()

        self.sip_conf._gen_user(pickup, user, ccss_options, output)

        self.assertIn('setvar = PICKUPMARK=101%mycontext', output.getvalue())

    def test__ccss_options_enabled(self):
        data_ccss = [{'commented': 0}]

        ccss_options = self.sip_conf._ccss_options(data_ccss)

        self.assertEqual('generic', ccss_options['cc_agent_policy'])
        self.assertEqual('generic', ccss_options['cc_monitor_policy'])
        self.assertEqual(sip.CC_OFFER_TIMER, ccss_options['cc_offer_timer'])
        self.assertEqual(sip.CC_RECALL_TIMER, ccss_options['cc_recall_timer'])
        self.assertEqual(sip.CCBS_AVAILABLE_TIMER, ccss_options['ccbs_available_timer'])
        self.assertEqual(sip.CCNR_AVAILABLE_TIMER, ccss_options['ccnr_available_timer'])

    def test__ccss_options_disabled(self):
        data_ccss = [{'commented': 1}]

        ccss_options = self.sip_conf._ccss_options(data_ccss)

        self.assertEqual('never', ccss_options['cc_agent_policy'])
        self.assertEqual('never', ccss_options['cc_monitor_policy'])
        self.assertNotIn('cc_offer_timer', ccss_options)
        self.assertNotIn('cc_recall_timer', ccss_options)
        self.assertNotIn('ccbs_available_timer', ccss_options)
        self.assertNotIn('ccnr_available_timer', ccss_options)