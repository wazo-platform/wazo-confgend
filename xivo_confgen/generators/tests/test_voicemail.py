# -*- coding: utf-8 -*-

# Copyright (C) 2012-2014 Avencall
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

import os
import StringIO
import unittest
from xivo_confgen.generators.voicemail import VoicemailConf
from xivo_confgen.generators.tests.util import parse_ast_config
from mock import patch, Mock


class TestVoicemailConf(unittest.TestCase):

    @patch('xivo_dao.asterisk_conf_dao.find_voicemail_general_settings', Mock(return_value=[]))
    @patch('xivo_dao.asterisk_conf_dao.find_voicemail_activated', Mock(return_value=[]))
    def setUp(self):
        self._output = StringIO.StringIO()
        self.voicemail_conf = VoicemailConf()
        self.voicemail_conf._voicemail_settings = []
        self.voicemail_conf._voicemails = []

    def _parse_ast_cfg(self):
        self._output.seek(os.SEEK_SET)
        return parse_ast_config(self._output)

    def test_empty_sections(self):
        self.voicemail_conf.generate(self._output)

        result = self._parse_ast_cfg()
        expected = {u'general': [],
                    u'zonemessages': []}
        self.assertEqual(expected, result)

    def test_one_element_general_section(self):
        self.voicemail_conf._voicemail_settings = [{'category': u'general',
                      'var_name': u'foo',
                      'var_val': u'bar'}]
        self.voicemail_conf.generate(self._output)

        result = self._parse_ast_cfg()
        expected = {u'general': [u'foo = bar'],
                    u'zonemessages': []}
        self.assertEqual(expected, result)

    def test_one_element_zonemessages_section(self):
        self.voicemail_conf._voicemail_settings = [{'category': u'zonemessages',
                      'var_name': u'foo',
                      'var_val': u'bar'}]
        self.voicemail_conf.generate(self._output)

        result = self._parse_ast_cfg()
        expected = {u'general': [],
                    u'zonemessages': [u'foo = bar']}
        self.assertEqual(expected, result)

    def test_escape_general_emailbody_option(self):
        self.voicemail_conf._voicemail_settings = [{'category': u'general',
                      'var_name': u'emailbody',
                      'var_val': u'foo\nbar'}]
        self.voicemail_conf.generate(self._output)

        result = self._parse_ast_cfg()
        expected = {u'general': [u'emailbody = foo\\nbar'],
                    u'zonemessages': []}
        self.assertEqual(expected, result)

    def test_one_mailbox(self):
        self.voicemail_conf._voicemails = [{'context': u'default',
                       'mailbox': u'm1',
                       'password': u'p1',
                       'fullname': u'Foo Bar',
                       'email': u'foo@example.org',
                       'pager': u''}]
        self.voicemail_conf.generate(self._output)

        result = self._parse_ast_cfg()
        expected = {u'general': [],
                    u'zonemessages': [],
                    u'default': [u'm1 => p1,Foo Bar,foo@example.org,,']}
        self.assertEqual(expected, result)

    def test_two_mailboxes_same_context(self):
        self.voicemail_conf._voicemails = [{'context': u'ctx1',
                       'mailbox': u'm1',
                       'password': u'',
                       'fullname': u'f1',
                       'email': u'',
                       'pager': u''},
                      {'context': u'ctx1',
                       'mailbox': u'm2',
                       'password': u'',
                       'fullname': u'f2',
                       'email': u'',
                       'pager': u''}]
        self.voicemail_conf.generate(self._output)

        result = self._parse_ast_cfg()
        expected = {u'general': [],
                    u'zonemessages': [],
                    u'ctx1': [u'm1 => ,f1,,,',
                              u'm2 => ,f2,,,']}
        self.assertEqual(expected, result)

    def test_two_mailboxes_different_context(self):
        self.voicemail_conf._voicemails = [{'context': u'ctx1',
                       'mailbox': u'm1',
                       'password': u'',
                       'fullname': u'f1',
                       'email': u'',
                       'pager': u''},
                      {'context': u'ctx2',
                       'mailbox': u'm2',
                       'password': u'',
                       'fullname': u'f2',
                       'email': u'',
                       'pager': u''},
                      ]
        self.voicemail_conf.generate(self._output)

        result = self._parse_ast_cfg()
        expected = {u'general': [],
                    u'zonemessages': [],
                    u'ctx1': [u'm1 => ,f1,,,'],
                    u'ctx2': [u'm2 => ,f2,,,']}
        self.assertEqual(expected, result)