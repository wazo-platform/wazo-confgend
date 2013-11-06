#!/usr/bin/python
# -*- coding: utf8 -*-

import ConfigParser
from twisted.application import service, internet
from twisted.python import usage
from twisted.internet import reactor
from xivo_confgen.confgen import ConfgendFactory


class Options(usage.Options):
    optParameters = [
        ['listen', 'l', '*', 'listen interface (* = all)', str],
        ['port', 'p', 5035, 'confgend server port', int],
        ['cache', 'a', '/var/lib/xivo-confgend', 'config cache', str],
        ['conf', 'c', '/etc/pf-xivo/xivo-confgend.conf', 'Configuration file', str],
    ]


def main():
    options = Options()
    options.parseOptions()

    config = ConfigParser.RawConfigParser()
    config.read(options['conf'])

    for key, value in config.items('confgend'):
        if key not in options.defaults:
            raise Exception("Unknown '%s' key in %s configuration file" % (key, options['conf']))

        # coerce value
        if key in options._dispatch:
            # NOTE: cannot directly use CoerceParameter.dispatch() as it affect result to opts dict
            try:
                value = options._dispatch[key].coerce(value)
            except ValueError:
                raise Exception("*%s* key in *%s* configuration file is invalid type" % (key, options['conf']))

        # replace if not set inline
        if options[key] == options.defaults[key]:
            options[key] = value

    if options['listen'] == '*':
        options['listen'] = ''

    f = ConfgendFactory(options['cache'], config)

    reactor.listenTCP(options['port'], f, interface=options['listen'])
    reactor.run()

    application = service.Application('confgend')
    service.IProcess(application).processName = "confgend"

    svc = internet.TCPServer(options['port'], f, interface=options['listen'])
    svc.setServiceParent(application)

if __name__ == '__main__':
    main()
