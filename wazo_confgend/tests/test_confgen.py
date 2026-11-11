# Copyright 2018-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


import random
import tempfile
import unittest
from unittest.mock import Mock, call, patch

from hamcrest import assert_that, calling, contains_exactly, equal_to, raises

from ..confgen import Confgen, ConfgendFactory


def sample_unicode_string(length):
    # Update this to include code point ranges to be sampled
    include_ranges = [
        (0x0021, 0x0021),
        (0x0023, 0x0026),
        (0x0028, 0x007E),
        (0x00A1, 0x00AC),
        (0x00AE, 0x00FF),
        (0x0100, 0x017F),
        (0x0180, 0x024F),
        (0x2C60, 0x2C7F),
        (0x16A0, 0x16F0),
        (0x0370, 0x0377),
        (0x037A, 0x037E),
        (0x0384, 0x038A),
        (0x038C, 0x038C),
        (0x0000, 0xFFFF),
    ]

    def select_range():
        start, end = random.choice(include_ranges)
        return range(start, end + 1)

    return ''.join(chr(random.choice(select_range())) for i in range(length))


class TestConfgen(unittest.TestCase):
    def setUp(self):
        self.factory = Mock()
        self.transport = Mock()
        self.protocol = Confgen()
        self.protocol.factory = self.factory
        self.protocol.transport = self.transport

    def test_receive_command(self):
        cmd = b'resource/filename.conf\n'

        self.protocol.dataReceived(cmd)

        self.factory.generate.assert_called_once_with('resource', 'filename.conf')
        self.transport.write.assert_called_once_with(
            self.factory.generate.return_value.encode("utf-8")
        )

    def test_receive_command_no_result(self):
        self.factory.generate.return_value = None
        cmd = b'resource/filename.conf\n'

        self.protocol.dataReceived(cmd)

        self.factory.generate.assert_called_once_with('resource', 'filename.conf')
        self.transport.write.assert_not_called()

    def test_receive_with_arguments(self):
        cmd = b'resource/filename.conf  arg1    arg2\n'

        self.protocol.dataReceived(cmd)

        self.factory.generate.assert_called_once_with(
            'resource', 'filename.conf', 'arg1', 'arg2'
        )
        self.transport.write.assert_called_once_with(
            self.factory.generate.return_value.encode("utf-8")
        )

    def test_receive_unicode(self):
        # randomly generated unicode string using sample_unicode_string
        filename = r'·ʹ©᛫¨Łã&ͻ!ͻͺ΄ÛͼⱧŎΌÁΌΌëŏᚵᛟⱦⱲ;×ᛘ&ǲ#ǒŽȸ¾ÝȗșΌýΌ#΄%ͽœͲgΌⱴͻÀOⱨΌ{ʹ±GǀᛊΌ!0͵ƕⱹͺⱤºⱪͷΌⱰᚩ#Ƶ#ÙᛊªÖʹ·ͼÑXƍ§Ɔ+ⱴ!§¤Vͷ£'
        cmd = f"resource/{filename}.conf arg1 arg2\n"
        self.protocol.dataReceived(cmd.encode("utf-8"))
        print(self.factory.generate.mock_calls)
        self.factory.generate.assert_called_with(
            'resource', f"{filename}.conf", 'arg1', 'arg2'
        )
        self.transport.write.assert_called_with(
            self.factory.generate.return_value.encode("utf-8")
        )

    def test_receive_bad_encoding(self):
        # test behavior when receiving non-utf-8 garbage
        # generated using os.urandom(20)
        cmd = b'\xferD\x86jJ)\xbf?\xdc\xfe\xa3\xf6l\xbd\x8cs\x0b\xdb\xa4'
        assert_that(
            calling(self.protocol.dataReceived).with_args(cmd),
            raises(UnicodeDecodeError),
        )


class TestConfgendFactory(unittest.TestCase):
    def setUp(self):
        config = {
            'templates': {'contextsconf': ''},
            'plugins': {},
        }
        cachedir = tempfile.gettempdir()

        self.factory = ConfgendFactory(cachedir, config)
        self.factory._handler_factory = self.handler_factory = Mock()
        self.handler = self.handler_factory.get.return_value
        self.get_cached_content = self.factory._get_cached_content = Mock()
        self.cache = self.factory._cache = Mock()

        session_scope_patcher = patch('wazo_confgend.confgen.session_scope')
        session_scope = session_scope_patcher.start()
        self.addCleanup(session_scope_patcher.stop)
        self.session = session_scope.return_value.__enter__.return_value

    def test_that_the_file_is_generated_from_one_snapshot(self):
        calls = Mock()
        calls.attach_mock(self.session.connection, 'connection')
        calls.attach_mock(self.handler, 'handler')

        self.factory.generate('test', 'myfile.yml')

        assert_that(
            calls.mock_calls,
            contains_exactly(
                call.connection(
                    execution_options={'isolation_level': 'REPEATABLE READ'}
                ),
                call.handler(),
            ),
        )

    def test_generate_from_handler(self):
        self.handler.return_value = 'some content'

        result = self.factory.generate('test', 'myfile.yml')

        assert_that(result, equal_to(self.handler.return_value))

    def test_that_error_on_generate_returns_cached_value(self):
        self.handler.side_effect = Exception
        self.get_cached_content.return_value = 'cached content'

        result = self.factory.generate('test', 'myfile.yml')

        assert_that(result, equal_to(self.get_cached_content.return_value))

    def test_that_the_cached_argument_returns_the_cached_value(self):
        self.handler.return_value = 'some content'
        self.get_cached_content.return_value = 'cached content'

        result = self.factory.generate('test', 'myfile.yml', 'cached')

        assert_that(result, equal_to(self.get_cached_content.return_value))

    def test_that_the_cached_argument_returns_the_a_generated_value_when_no_cache(self):
        self.handler.return_value = 'some content'
        self.get_cached_content.return_value = None

        result = self.factory.generate('test', 'myfile.yml', 'cached')

        assert_that(result, equal_to(self.handler.return_value))

    def test_the_invalidate_command(self):
        result = self.factory.generate('test', 'myfile.yml', 'invalidate')

        assert_that(result, equal_to(None))
        self.cache.invalidate.assert_called_once_with('test/myfile.yml')
