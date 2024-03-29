# Copyright 2013-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from xivo_dao import asterisk_conf_dao

from wazo_confgend.generators.util import AsteriskFileWriter


class QueuesConf:
    _ignored_keys = [
        'name',
        'label',
        'category',
        'commented',
    ]

    def generate(self, output):
        writer = AsteriskFileWriter(output)

        writer.write_section('general')
        for item in asterisk_conf_dao.find_queue_general_settings():
            writer.write_option(item['var_name'], item['var_val'])

        for q in asterisk_conf_dao.find_queue_settings():
            writer.write_section(q['name'], comment=q['label'])

            for k, v in q.items():
                if k in self._ignored_keys:
                    continue
                if v is None or (isinstance(v, str) and not v):
                    continue

                writer.write_option(k, v)

            queuemember_settings = asterisk_conf_dao.find_queue_members_settings(
                q['name']
            )
            for values in queuemember_settings:
                writer.write_option('member', ','.join(values))
