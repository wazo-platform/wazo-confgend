# -*- coding: utf-8 -*-

# Copyright (C) 2011-2016 Avencall
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

import time
import sys

from stevedore import driver, exception

from xivo_confgen import cache
from xivo_confgen.asterisk import AsteriskFrontend
from xivo_confgen.xivo import XivoFrontend
from xivo_confgen.dird import DirdFrontend
from xivo_confgen.dird_phoned import DirdPhonedFrontend
from xivo_dao.helpers.db_utils import session_scope
from twisted.internet.protocol import Protocol, ServerFactory


class Confgen(Protocol):

    def dataReceived(self, data):
        try:
            t1 = time.time()
            self._write_response(data)
            t2 = time.time()

            print "serving %s in %.3f seconds" % (data, t2 - t1)
        finally:
            self.transport.loseConnection()

    def _write_response(self, data):
        if data[-1] == '\n':
            data = data[:-1]

        # 'asterisk/sip.conf' => ('asterisk', 'sip_conf')
        content = self._content_from_plugin(data)
        if not content:
            content = self._content_from_frontend(data)

        if content is None:
            # get cache content
            print "cache hit on %s" % data
            try:
                content = self.factory.cache.get(data).decode('utf8')
            except AttributeError:
                print "No such configuration for %s" % data
                return
        else:
            # write to cache
            self.factory.cache.put(data, content.encode('utf8'))

        self.transport.write(content.encode('utf8'))

    def _content_from_frontend(self, data):
        try:
            (frontend_name, callback) = data.split('/')
            callback = callback.replace('.', '_')
        except Exception:
            print "cannot split"
            return

        frontend = self.factory.frontends.get(frontend_name)
        if frontend is None:
            print "no such frontend %r" % frontend_name
            return

        try:
            with session_scope():
                return getattr(frontend, callback)()
        except Exception as e:
            import traceback
            print e
            traceback.print_exc(file=sys.stdout)

    def _content_from_plugin(self, data):
        suffix = data.replace('/', '.')
        namespace = 'confgend.{}'.format(suffix)
        driver_name = self._config['plugins'].get(suffix)
        if not driver_name:
            print 'No plugin configuration found for namespace {}'.format(namespace)
            return None

        try:
            mgr = driver.DriverManager(
                namespace=namespace,
                name=driver_name,
                invoke_on_load=True,
                invoke_args=(self._config,))
        except exception.NoMatches:
            print 'No plugin found in {} with name {}'.format(namespace, driver_name)
        else:
            return mgr.driver.generate()


class ConfgendFactory(ServerFactory):

    protocol = Confgen

    def __init__(self, cachedir, config):
        self.protocol._config = config
        self.frontends = {
            'asterisk': AsteriskFrontend(config),
            'dird': DirdFrontend(),
            'dird-phoned': DirdPhonedFrontend(),
            'xivo': XivoFrontend(),
        }
        self.cache = cache.FileCache(cachedir)
