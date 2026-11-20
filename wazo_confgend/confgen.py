# Copyright 2011-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
import time

import twisted.python.failure
from twisted.internet.protocol import Protocol, ServerFactory
from xivo_dao.helpers.db_utils import session_scope

from wazo_confgend import cache
from wazo_confgend.asterisk import AsteriskFrontend
from wazo_confgend.handler import (
    CachedHandlerFactoryDecorator,
    FrontendHandlerFactory,
    MultiHandlerFactory,
    NullHandlerFactory,
    PluginHandlerFactory,
)
from wazo_confgend.phoned import PhonedFrontend
from wazo_confgend.template import new_template_helper
from wazo_confgend.wazo import WazoFrontend

logger = logging.getLogger(__name__)


class Confgen(Protocol):
    def connectionMade(self):
        logger.info("connection established")

    def connectionLost(self, reason: twisted.python.failure.Failure):
        logger.info("connection lost: %s", reason.getErrorMessage())
        super().connectionLost(reason=reason)

    def commandReceived(self, cmd: str, args: list[str]):
        logger.debug(
            "command received cmd_length=%d, args_count=%d", len(cmd), len(args)
        )
        try:
            resource, filename = cmd.split('/')
        except ValueError:
            logger.error("cannot split %s", cmd)
            return

        content = self.factory.generate(resource, filename, *args)
        if content:
            self.transport.write(content.encode("utf-8"))

    def dataReceived(self, data: bytes):
        logger.debug("data received bytes_count=%d", len(data))

        data = data.decode("utf-8")
        try:
            t1 = time.time()
            line = data.replace('\n', '')

            if ' ' in line:
                cmd, trailing = line.split(' ', 1)
                args = [arg for arg in trailing.split(' ') if arg]
            else:
                cmd, args = line, []

            self.commandReceived(cmd, args)

            t2 = time.time()

            logger.info("serving %s in %.3f seconds", line, t2 - t1)
        finally:
            self.transport.loseConnection()


class ConfgendFactory(ServerFactory):
    protocol = Confgen

    def __init__(self, cachedir, config):
        tpl_helper = new_template_helper()
        dependencies = {
            'config': config,
            'tpl_helper': tpl_helper,
        }
        frontends = {
            'asterisk': AsteriskFrontend(config, tpl_helper),
            'phoned': PhonedFrontend(),
            'wazo': WazoFrontend(),
        }
        self._cache = cache.FileCache(cachedir)
        self._handler_factory = MultiHandlerFactory(
            [
                CachedHandlerFactoryDecorator(
                    PluginHandlerFactory(config, dependencies)
                ),
                FrontendHandlerFactory(frontends),
                NullHandlerFactory(),
            ]
        )

    def generate(self, resource, filename, *args):
        logger.info(
            "Generating conf for resource=%s and filename=%s with args=%s",
            resource,
            filename,
            args,
        )
        cache_key = f'{resource}/{filename}'
        if 'invalidate' in args:
            self._cache.invalidate(cache_key)
        elif 'cached' in args:
            return self._get_cached_content(cache_key) or self._generate_and_cache(
                cache_key, resource, filename
            )
        else:
            return self._generate_and_cache(
                cache_key, resource, filename
            ) or self._get_cached_content(cache_key)

    def _generate_and_cache(self, cache_key, resource, filename):
        handler = self._handler_factory.get(resource, filename)
        with session_scope(read_only=True) as session:
            try:
                session.connection(
                    execution_options={'isolation_level': 'REPEATABLE READ'}
                )
                content = handler()
                return self._encode_and_cache(cache_key, content)
            except Exception:
                logger.error('unexpected error raised by handler', exc_info=True)

    def _get_cached_content(self, cache_key):
        try:
            return self._cache.get(cache_key)
        except AttributeError:
            logger.warning("No cached content for %s", cache_key)

    def _encode_and_cache(self, cache_key, content):
        if not content:
            return

        encoded_content = content
        self._cache.put(cache_key, encoded_content)
        return encoded_content
