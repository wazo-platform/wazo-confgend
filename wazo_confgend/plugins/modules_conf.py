# Copyright 2019-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


import logging

from jinja2 import Template

logger = logging.getLogger(__name__)


class ModulesConfGenerator:
    def __init__(self, dependencies):
        config = dependencies['config']

        asterisk_modules = config.get('enabled_asterisk_modules', {})
        self._disabled_asterisk_modules = sorted(
            [mod for mod, enabled in list(asterisk_modules.items()) if not enabled]
        )

        self.template_filename = config['templates']['modulesconf']

    def generate(self):
        try:
            with open(self.template_filename) as f:
                raw = f.read()
                template = Template(raw)
        except OSError as e:
            logger.error('%s', e)
            content = None
        else:
            content = template.render(modules=self._disabled_asterisk_modules)
        return content
