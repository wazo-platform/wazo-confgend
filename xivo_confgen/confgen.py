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

import time
import sys
from xivo_confgen import cache
from xivo_confgen.asterisk import AsteriskFrontend
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
        try:
            (frontend, callback) = data.split('/')
            callback = callback.replace('.', '_')
        except Exception:
            print "cannot split"
            return

        try:
            content = getattr(self.factory.asterisk_frontend, callback)()
        except Exception as e:
            import traceback
            print e
            traceback.print_exc(file=sys.stdout)
            content = None

        if content is None:
            # get cache content
            print "cache hit on %s" % data
            try:
                content = self.factory.cache.get(data).decode('utf8')
            except AttributeError, e:
                print "No such configuration for %s" % data
                return
        else:
            # write to cache
            self.factory.cache.put(data, content.encode('utf8'))

        self.transport.write(content.encode('utf8'))


class ConfgendFactory(ServerFactory):
    protocol = Confgen

    def __init__(self, cachedir, config):
        self.asterisk_frontend = self._new_asterisk_frontend(config)
        self.cache = cache.FileCache(cachedir)

    def _new_asterisk_frontend(self, config):
        asterisk_frontend = AsteriskFrontend()
        asterisk_frontend.contextsconf = config.get('asterisk', 'contextsconf')
        return asterisk_frontend