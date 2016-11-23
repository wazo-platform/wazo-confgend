# -*- coding: utf-8 -*-

# Copyright (C) 2016 Avencall
# Copyright (C) 2016 Proformatique Inc.
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

from __future__ import unicode_literals

import logging

from collections import namedtuple
from StringIO import StringIO

from xivo_dao import asterisk_conf_dao

CC_POLICY_ENABLED = 'generic'
CC_POLICY_DISABLED = 'never'
CC_OFFER_TIMER = 30
CC_RECALL_TIMER = 20
CCBS_AVAILABLE_TIMER = 900
CCNR_AVAILABLE_TIMER = 900
COMMON_EXCLUDE_OPTIONS = (
    'name',
    'protocol',
    'category',
    'disallow',
)

logger = logging.getLogger(__name__)


class SIPConfGenerator(object):

    def __init__(self, dependencies):
        config = dependencies['config']
        self._nova_compatibility = config['nova_compatibility']
        self._tpl_helper = dependencies['tpl_helper']

    def generate(self):
        twilio_config_generator = _TwilioConfigGenerator(self._tpl_helper)
        trunk_generator = _SipTrunkGenerator(asterisk_conf_dao, twilio_config_generator)
        user_generator = _SipUserGenerator(asterisk_conf_dao, nova_compatibility=self._nova_compatibility)
        config_generator = _SipConf(trunk_generator, user_generator)
        output = StringIO()
        config_generator.generate(output)
        return output.getvalue()


class _SipUserGenerator(object):

    EXCLUDE_OPTIONS = COMMON_EXCLUDE_OPTIONS

    def __init__(self, dao, nova_compatibility=False):
        self.dao = dao
        self._nova_compatibility = nova_compatibility

    def generate(self, ccss_options):
        for row in self.dao.find_sip_user_settings():
            for line in self.format_row(row, ccss_options):
                yield line

    def format_row(self, row, ccss_options):
        yield '[{}]'.format(row.UserSIP.name)
        yield 'setvar = CHANNEL(hangup_handler_push)=hangup_handlers,userevent,1'

        for line in self.format_user_options(row):
            yield line
        for line in self.format_options(ccss_options.iteritems()):
            yield line

        options = row.UserSIP.all_options(self.EXCLUDE_OPTIONS)
        for line in self.format_allow_options(options):
            yield line
        for line in self.format_options(options):
            yield line

        yield ''

    def format_user_options(self, row):
        yield 'setvar = XIVO_ORIGINAL_CALLER_ID={}'.format(row.UserSIP.callerid)
        if row.context:
            yield 'setvar = TRANSFER_CONTEXT={}'.format(row.context)
        if row.number and row.context:
            yield 'setvar = PICKUPMARK={}%{}'.format(row.number, row.context)
        if row.user_id:
            yield 'setvar = XIVO_USERID={}'.format(row.user_id)
        if row.uuid:
            yield 'setvar = XIVO_USERUUID={}'.format(row.uuid)
        if row.namedpickupgroup:
            yield 'namedpickupgroup = {}'.format(row.namedpickupgroup)
        if row.namedcallgroup:
            yield 'namedcallgroup = {}'.format(row.namedcallgroup)
        if row.mohsuggest:
            yield 'mohsuggest = {}'.format(row.mohsuggest)
        if row.mailbox:
            yield 'mailbox = {}'.format(row.mailbox)
        if row.UserSIP.callerid:
            yield 'description = {}'.format(row.UserSIP.callerid)
        if self._nova_compatibility and row.number:
            yield 'accountcode = {}'.format(row.number)

    def format_allow_options(self, options):
        allow_found = 'allow' in (option_name for option_name, _ in options)
        if allow_found:
            yield 'disallow = all'

    def format_options(self, options):
        for name, value in options:
            yield '{} = {}'.format(name, value)


class _SipTrunkGenerator(object):

    EXCLUDE_OPTIONS = COMMON_EXCLUDE_OPTIONS

    def __init__(self, dao, twilio_config_generator):
        self.dao = dao
        self._twilio_config_generator = twilio_config_generator

    def generate(self):
        trunks = self.dao.find_sip_trunk_settings()
        yield self._twilio_config_generator.generate(trunks)
        for trunk in trunks:
            for line in self.format_trunk(trunk.UserSIP):
                yield line

    def format_trunk(self, trunk):
        options = trunk.all_options(exclude=self.EXCLUDE_OPTIONS)
        allow_present = 'allow' in (option_name for option_name, _ in options)

        yield '[{}]'.format(trunk.name)

        if allow_present:
            yield 'disallow = all'

        for name, value in options:
            yield '{} = {}'.format(name, value)

        yield ''


_TwilioGateway = namedtuple('_TwilioGateway', ['ip_address', 'cluster_name'])


class _TwilioConfigGenerator(object):

    TWILIO_GATEWAYS = [
        # see https://www.twilio.com/docs/api/sip-trunking/getting-started#whitelist
        _TwilioGateway('54.172.60.0', 'north-america-virginia'),
        _TwilioGateway('54.172.60.1', 'north-america-virginia'),
        _TwilioGateway('54.172.60.2', 'north-america-virginia'),
        _TwilioGateway('54.172.60.3', 'north-america-virginia'),
        _TwilioGateway('54.244.51.0', 'north-america-oregon'),
        _TwilioGateway('54.244.51.1', 'north-america-oregon'),
        _TwilioGateway('54.244.51.2', 'north-america-oregon'),
        _TwilioGateway('54.244.51.3', 'north-america-oregon'),
        _TwilioGateway('54.171.127.192', 'europe-ireland'),
        _TwilioGateway('54.171.127.193', 'europe-ireland'),
        _TwilioGateway('54.171.127.194', 'europe-ireland'),
        _TwilioGateway('54.171.127.195', 'europe-ireland'),
        _TwilioGateway('54.65.63.192', 'asia-pacific-tokyo'),
        _TwilioGateway('54.65.63.193', 'asia-pacific-tokyo'),
        _TwilioGateway('54.65.63.194', 'asia-pacific-tokyo'),
        _TwilioGateway('54.65.63.195', 'asia-pacific-tokyo'),
        _TwilioGateway('54.169.127.128', 'asia-pacific-singapore'),
        _TwilioGateway('54.169.127.129', 'asia-pacific-singapore'),
        _TwilioGateway('54.169.127.130', 'asia-pacific-singapore'),
        _TwilioGateway('54.169.127.131', 'asia-pacific-singapore'),
        _TwilioGateway('54.252.254.64', 'asia-pacific-sydney'),
        _TwilioGateway('54.252.254.65', 'asia-pacific-sydney'),
        _TwilioGateway('54.252.254.66', 'asia-pacific-sydney'),
        _TwilioGateway('54.252.254.67', 'asia-pacific-sydney'),
        _TwilioGateway('177.71.206.192', 'south-america-sao-paulo'),
        _TwilioGateway('177.71.206.193', 'south-america-sao-paulo'),
        _TwilioGateway('177.71.206.194', 'south-america-sao-paulo'),
        _TwilioGateway('177.71.206.195', 'south-america-sao-paulo'),
    ]
    EXCLUDE_OPTIONS = COMMON_EXCLUDE_OPTIONS + ('type',
                                                'description',
                                                'defaultuser',
                                                'host',
                                                'qualify',
                                                'secret',
                                                'subscribemwi',
                                                'username')

    def __init__(self, tpl_helper):
        self._tpl_helper = tpl_helper

    def generate(self, trunks):
        # the order is important in the case there's more than
        # one "twilio incoming trunk": the first one is used
        trunk = self._find_twilio_incoming_trunk(trunks)
        if trunk is None:
            return ''

        logger.info('generating Twilio config using trunk %s', trunk.UserSIP.name)
        template_context = {
            'endpoint': trunk.UserSIP,
            'exclude_options': self.EXCLUDE_OPTIONS,
            'gateways': self.TWILIO_GATEWAYS,
        }
        template = self._tpl_helper.get_template('asterisk/sip/twilio')
        return template.dump(template_context)

    def _find_twilio_incoming_trunk(self, trunks):
        for trunk in trunks:
            if trunk.twilio_incoming:
                return trunk
        return None


class _SipConf(object):

    def __init__(self, trunk_generator, user_generator):
        self.trunk_generator = trunk_generator
        self.user_generator = user_generator

    def generate(self, output):
        self._generate(output)

    def _generate(self, output):
        data_general = asterisk_conf_dao.find_sip_general_settings()
        self._gen_general(data_general, output)
        print >> output

        data_auth = asterisk_conf_dao.find_sip_authentication_settings()
        self._gen_authentication(data_auth, output)
        print >> output

        self._gen_trunk(output)
        print >> output

        data_ccss = asterisk_conf_dao.find_extenfeatures_settings(['cctoggle'])
        ccss_options = self._ccss_options(data_ccss)
        self._gen_user(ccss_options, output)

        print >> output

    def _gen_general(self, data_general, output):
        print >> output, '[general]'
        for item in data_general:
            if item['var_val'] is None:
                continue

            if item['var_name'] in ('register', 'mwi'):
                print >> output, item['var_name'], "=>", item['var_val']

            elif item['var_name'] == 'prematuremedia':
                var_val = 'yes' if item['var_val'] == 'no' else 'no'
                print >> output, item['var_name'], "=", var_val

            elif item['var_name'] not in ['allow', 'disallow']:
                print >> output, item['var_name'], "=", item['var_val']

            elif item['var_name'] == 'allow':
                print >> output, 'disallow = all'
                print >> output, 'allow =', item['var_val']

    def _gen_authentication(self, data_authentication, output):
        if len(data_authentication) > 0:
            print >> output, '\n[authentication]'
            for auth in data_authentication:
                mode = '#' if auth['secretmode'] == 'md5' else ':'
                print >> output, "auth = %s%s%s@%s" % (auth['user'], mode, auth['secret'], auth['realm'])

    def _gen_trunk(self, output):
        for line in self.trunk_generator.generate():
            print >> output, line

    def _gen_user(self, ccss_options, output):
        for line in self.user_generator.generate(ccss_options):
            print >> output, line

    def _ccss_options(self, data_ccss):
        if data_ccss:
            ccss_info = data_ccss[0]
            if ccss_info.get('commented') == 0:
                return {
                    'cc_agent_policy': CC_POLICY_ENABLED,
                    'cc_monitor_policy': CC_POLICY_ENABLED,
                    'cc_offer_timer': CC_OFFER_TIMER,
                    'cc_recall_timer': CC_RECALL_TIMER,
                    'ccbs_available_timer': CCBS_AVAILABLE_TIMER,
                    'ccnr_available_timer': CCNR_AVAILABLE_TIMER,
                }

        return {
            'cc_agent_policy': CC_POLICY_DISABLED,
            'cc_monitor_policy': CC_POLICY_DISABLED,
        }


def gen_value_line(key, value):
    return '%s = %s' % (key, unicodify_string(value))


def unicodify_string(to_unicodify):
    try:
        return unicode(to_unicodify)
    except UnicodeDecodeError:
        return to_unicodify.decode('utf8')
