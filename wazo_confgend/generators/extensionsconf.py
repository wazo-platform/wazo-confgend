# Copyright 2011-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import configparser
import logging

from xivo import xivo_helpers
from xivo_dao import asterisk_conf_dao
from xivo_dao.resources.ivr import dao as ivr_dao

from wazo_confgend.generators.util import AsteriskFileWriter
from wazo_confgend.helpers.asterisk import asterisk_parser

logger = logging.getLogger(__name__)


DEFAULT_EXTENFEATURES = {
    'paging': 'GoSub(paging,s,1(${EXTEN:3}))',
    'autoprov': 'GoSub(autoprov,s,1())',
    'incallfilter': 'GoSub(incallfilter,s,1())',
    'phoneprogfunckey': 'GoSub(phoneprogfunckey,s,1(${EXTEN:0:4},${EXTEN:4}))',
    'phonestatus': 'GoSub(phonestatus,s,1())',
    'pickup': 'GoSub(wazo-pickup,s,1(${EXTEN:2},${CONTEXT}))',
    'recsnd': 'GoSub(recsnd,s,1(wav))',
    'vmboxmsgslt': 'GoSub(vmboxmsg,s,1(${EXTEN:3}))',
    'vmboxpurgeslt': 'GoSub(vmboxpurge,s,1(${EXTEN:3}))',
    'vmboxslt': 'GoSub(vmbox,s,1(${EXTEN:3}))',
    'vmusermsg': 'GoSub(vmusermsg,s,1())',
    'vmuserpurge': 'GoSub(vmuserpurge,s,1())',
    'vmuserpurgeslt': 'GoSub(vmuserpurge,s,1(${EXTEN:3}))',
    'vmuserslt': 'GoSub(vmuser,s,1(${EXTEN:3}))',
    'agentstaticlogin': 'GoSub(agentstaticlogin,s,1(${EXTEN:3}))',
    'agentstaticlogoff': 'GoSub(agentstaticlogoff,s,1(${EXTEN:3}))',
    'agentstaticlogtoggle': 'GoSub(agentstaticlogtoggle,s,1(${EXTEN:3}))',
    'bsfilter': 'GoSub(bsfilter,s,1(${EXTEN:3}))',
    'meetingjoin': 'GoSub(meetingjoin,s,1(${EXTEN:3}))',
    'callrecord': 'GoSub(callrecord,s,1() )',
    'directoryaccess': 'Directory(${CONTEXT})',
    'enablednd': 'GoSub(enablednd,s,1())',
    'enablevm': 'GoSub(enablevm,s,1())',
    'enablevmslt': 'GoSub(enablevm,s,1(${EXTEN:3}))',
    'fwdundoall': 'GoSub(fwdundoall,s,1())',
    'fwdbusy': 'GoSub(feature_forward,s,1(busy,${EXTEN:3}))',
    'fwdrna': 'GoSub(feature_forward,s,1(rna,${EXTEN:3}))',
    'fwdunc': 'GoSub(feature_forward,s,1(unc,${EXTEN:3}))',
    'groupmembertoggle': 'GoSub(group-member-toggle,s,1(${EXTEN:3}))',
    'groupmemberjoin': 'GoSub(group-member-join,s,1(${EXTEN:3}))',
    'groupmemberleave': 'GoSub(group-member-leave,s,1(${EXTEN:3}))',
}


class ExtensionGenerator:
    def __init__(self, exten_row):
        self._exten_row = exten_row


class UserExtensionGenerator(ExtensionGenerator):
    def generate(self):
        return {
            'tenant_uuid': self._exten_row['tenant_uuid'],
            'context': self._exten_row['context'],
            'exten': self._exten_row['exten'],
            'priority': '1',
            'action': 'GoSub(user,s,1({},,{}))'.format(
                self._exten_row['typeval'], self._exten_row['id']
            ),
        }


class IncallExtensionGenerator(ExtensionGenerator):
    def generate(self):
        return {
            'tenant_uuid': self._exten_row['tenant_uuid'],
            'context': self._exten_row['context'],
            'exten': self._exten_row['exten'],
            'priority': '1',
            'action': f"GoSub(did,s,1({self._exten_row['typeval']},))",
        }


class GenericExtensionGenerator(ExtensionGenerator):
    def generate(self):
        return {
            'tenant_uuid': self._exten_row['tenant_uuid'],
            'context': self._exten_row['context'],
            'exten': self._exten_row['exten'],
            'priority': '1',
            'action': 'GoSub({},s,1({},))'.format(
                self._exten_row['type'], self._exten_row['typeval']
            ),
        }


extension_generators = {
    'user': UserExtensionGenerator,
    'incall': IncallExtensionGenerator,
    'did': IncallExtensionGenerator,
}


class ExtensionsConf:
    def __init__(self, contextsconf, hint_generator, tpl_helper):
        self.contextsconf = contextsconf
        self.hint_generator = hint_generator
        self._tpl_helper = tpl_helper

    def generate(self, output):
        ast_writer = AsteriskFileWriter(output)
        conf = asterisk_parser()

        if self.contextsconf is not None:
            # load and validate template conf
            try:
                with open(self.contextsconf) as contextsconf_file:
                    conf.read_file(contextsconf_file)
            except configparser.DuplicateSectionError:
                raise ValueError(f"{self.contextsconf} has conflicting section names")

            if not conf.has_section('template'):
                raise ValueError(
                    f"Template section doesn't exist in {self.contextsconf}"
                )

        # hints & features (init)
        self._generate_global_hints(output)
        extenfeature_names = (
            'bsfilter',
            'fwdbusy',
            'fwdrna',
            'fwdunc',
            'phoneprogfunckey',
            'vmusermsg',
        )
        extenfeatures = asterisk_conf_dao.find_extenfeatures_settings(
            features=extenfeature_names
        )
        xfeatures = {
            extenfeature.feature: {
                'exten': extenfeature.exten,
                'enabled': extenfeature.enabled,
            }
            for extenfeature in extenfeatures
        }

        # foreach active context
        for ctx in asterisk_conf_dao.find_context_settings():
            # context name preceded with '!' is ignored
            context_name = ctx['name']
            if conf and conf.has_section(f'!{context_name}'):
                continue
            ast_writer.write_newline()
            ast_writer.write_section(context_name)
            if conf.has_section(context_name):
                section = context_name
            elif conf.has_section(f"type:{ctx['contexttype']}"):
                section = f"type:{ctx['contexttype']}"
            else:
                section = 'template'

            tmpl = []
            for option_name, option_value in conf.items(section):
                if option_name == 'objtpl':
                    tmpl.append(option_value)
                    continue
                ast_writer.write_option(
                    option_name, option_value.replace('%%CONTEXT%%', context_name)
                )

            # context includes
            for row in asterisk_conf_dao.find_contextincludes_settings(context_name):
                ast_writer.write_option('include', row['include'])
            ast_writer.write_newline()

            # objects extensions (user, group, ...)
            for exten_row in asterisk_conf_dao.find_exten_settings(context_name):
                exten_generator = extension_generators.get(
                    exten_row['type'], GenericExtensionGenerator
                )
                exten = exten_generator(exten_row).generate()
                self.gen_dialplan_from_template(tmpl, exten, ast_writer)

            self._generate_hints(ctx['name'], output)

        self._generate_extension_features(conf, xfeatures, ast_writer)
        self._generate_ivr(output)

        return output.getvalue()

    def _generate_extension_features(self, conf, xfeatures, ast_writer):
        # XiVO features
        context = 'xivo-features'
        cfeatures = []
        tmpl = []
        ast_writer.write_section(context)
        for option_name, option_value in conf.items(context):
            if option_name == 'objtpl':
                tmpl.append(option_value)
                continue
            ast_writer.write_option(
                option_name, option_value.replace('%%CONTEXT%%', context)
            )
            ast_writer.write_newline()

        for exten in asterisk_conf_dao.find_exten_xivofeatures_setting():
            feature = exten['feature']
            if feature in DEFAULT_EXTENFEATURES:
                exten['action'] = DEFAULT_EXTENFEATURES[feature]
                exten['context'] = context
                self.gen_dialplan_from_template(tmpl, exten, ast_writer)

        for x in ('busy', 'rna', 'unc'):
            fwdtype = f"fwd{x}"
            if xfeatures[fwdtype].get('enabled', False):
                exten = xivo_helpers.clean_extension(xfeatures[fwdtype]['exten'])
                cfeatures.extend(
                    [
                        "%s,1,Set(__WAZO_BASE_CONTEXT=${CONTEXT})" % exten,
                        "%s,n,Set(__XIVO_BASE_EXTEN=${EXTEN})" % exten,
                        f"{exten},n,Gosub(feature_forward,s,1({x}))\n",
                    ]
                )

        if cfeatures:
            for exten_feature in cfeatures:
                ast_writer.write_option('exten', exten_feature)

    def gen_dialplan_from_template(self, template, exten, ast_writer):
        if 'priority' not in exten:
            exten['priority'] = 1

        for line in template:
            prefix, padding = (
                ('exten', '') if line.startswith('%%EXTEN%%') else ('same ', '    ')
            )

            line = line.replace('%%CONTEXT%%', str(exten.get('context', '')))
            line = line.replace('%%EXTEN%%', str(exten.get('exten', '')))
            line = line.replace('%%PRIORITY%%', str(exten.get('priority', '')))
            line = line.replace('%%ACTION%%', str(exten.get('action', '')))
            line = line.replace('%%TENANT_UUID%%', str(exten.get('tenant_uuid', '')))

            ast_writer.write_option(prefix, f'{padding}{line}')
        ast_writer.write_newline()

    def _generate_global_hints(self, output):
        output.write('[usersharedlines]\n')
        for line in self.hint_generator.generate_global_hints():
            output.write(f'{line}\n')

    def _generate_hints(self, context, output):
        for line in self.hint_generator.generate(context):
            output.write(f'{line}\n')

    def _generate_ivr(self, output):
        for ivr in ivr_dao.find_all_by():
            template_context = {'ivr': ivr}
            template = self._tpl_helper.get_customizable_template(
                'asterisk/extensions/ivr', ivr.id
            )
            output.write(f'{template.dump(template_context)}\n')
