from twisted.internet import task
from twisted.test import proto_helpers
from twisted.trial import unittest

from wlmetaserver import MetaServer, MSConnection, make_packet
from wlms.db.flatfile import FlatFileDatabase

# Helper classes  {{{
class _Base(object):
    def setUp(self):
        db = FlatFileDatabase("SirVer\t123456\tSUPERUSER\n" + "otto\tottoiscool\tREGISTERED\n")
        self.ms = MetaServer(db)
        self.clock = task.Clock()
        self._cons = [ self.ms.buildProtocol(('127.0.0.1', 0)) for i in range(10) ]
        self._trs = [ proto_helpers.StringTransport() for i in range(10) ]
        for c,tr in zip(self._cons, self._trs):
            c.callLater = self.clock.callLater
            c.makeConnection(tr)

    def tearDown(self):
        for idx,c in enumerate(self._cons):
            p = self._recv(idx)
            if p:
                raise RuntimeError("unexpected packet from client %i: %r" % (idx, p))

    def _recv(self, client):
        d = self._trs[client].value()
        self._trs[client].clear()
        rv = []
        while len(d):
            size = (ord(d[0]) << 8) + ord(d[1])
            self.assertTrue(size <= len(d))
            rv.append(d[2:size][:-1].split("\x00"))
            d = d[size:]
        return rv

    def _mult_receive(self, clients):
        """Make sure everybody received the same data,
        return this data once"""
        ps = [ self._recv(c) for c in clients ]
        for idx,p in enumerate(ps[1:], 1):
            self.assertEqual(ps[idx-1], ps[idx])
        return ps[0]

    def _send(self, client, *args, **kwargs):
        c = self._cons[client]
        c.dataReceived(make_packet(*args))
# End: Helper classes  }}}

# Send Garbage  {{{
class TestGarbage(_Base, unittest.TestCase):
    def test_sending_absolute_garbage_too_short(self):
        self._cons[0].dataReceived("\xff")
        self.assertFalse(self._recv(0))
    def test_sending_absolute_garbage(self):
        self._cons[0].dataReceived("\xff\x37lkjdflsjflkjsf")
        self.assertFalse(self._recv(0))
    def test_sending_nonexisting_packet(self):
        self._send(0, "BLUMBAQUATSCH")
        p1, = self._recv(0)
        self.assertEqual(p1, ['ERROR', 'GARBAGE_RECEIVED', "Invalid or forbidden command: 'BLUMBAQUATSCH'"])
    def test_sending_toolittle_arguments_packet(self):
        self._send(0, "LOGIN", "hi")
        p1, = self._recv(0)
        self.assertEqual(p1, ['ERROR', 'LOGIN', "Invalid integer: 'hi'"])
# End: Send Garbage  }}}

# Test Login  {{{
class TestLogin(_Base, unittest.TestCase):
    def test_loginanon(self):
        self._send(0, "LOGIN", 0, "testuser", "build-17", "false")
        p1,p2,p3 = list(self._recv(0))
        self.assertEqual(p1, ['LOGIN', 'testuser', "UNREGISTERED"])
        self.assertEqual(p2[0], 'TIME')
        self.assertEqual(p3, ['CLIENTS_UPDATE'])

    def test_loginanon_withknownusername(self):
        self._send(0, "LOGIN", 0, "SirVer", "build-17", "false")
        p1,p2,p3 = list(self._recv(0))
        self.assertEqual(p1, ['LOGIN', 'SirVer1', "UNREGISTERED"])
        self.assertEqual(p2[0], 'TIME')
        self.assertEqual(p3, ['CLIENTS_UPDATE'])

    def test_loginanon_onewasalreadythere(self):
        # Login client 0
        self._send(0, "LOGIN", 0, "testuser", "build-17", "false")
        p1, p2, p3 = self._recv(0)
        self.assertEqual(p1, ['LOGIN', 'testuser', "UNREGISTERED"])
        self.assertEqual(p2[0], 'TIME')
        self.assertEqual(p3, ['CLIENTS_UPDATE'])

        # Login client 1
        self._send(1, "LOGIN", 0, "testuser", "build-17", "false")
        p1, p2, p3 = self._recv(1)
        # Note: Other username
        self.assertEqual(p1, ['LOGIN', 'testuser1', "UNREGISTERED"])
        self.assertEqual(p2[0], 'TIME')
        self.assertEqual(p3, ['CLIENTS_UPDATE'])

        # 0 should get an CLIENTS_UPDATE
        p1, = self._recv(0)
        self.assertEqual(p1, ['CLIENTS_UPDATE'])

    def test_nonanon_login_correct_password(self):
        self._send(0, "LOGIN", 0, "SirVer", "build-17", 1, "123456")
        p1, p2, p3 = self._recv(0)
        self.assertEqual(p1, ['LOGIN', 'SirVer', "SUPERUSER"])
        self.assertEqual(p2[0], 'TIME')
        self.assertEqual(p3, ['CLIENTS_UPDATE'])

    def test_nonanon_login_onewasalreadythere(self):
        # Login client 0
        self._send(0, "LOGIN", 0, "SirVer", "build-17", 1, "123456")
        self._recv(0)

        # Login client 0
        self._send(1, "LOGIN", 0, "SirVer", "build-17", 1, "123456")
        p1, = self._recv(1)

        self.assertEqual(p1, ['ERROR', 'LOGIN', 'ALREADY_LOGGED_IN'])

    def test_nonanon_login_twousers_password(self):
        self._send(0, "LOGIN", 0, "SirVer", "build-17", 1, "123456")
        p1, p2, p3 = self._recv(0)
        self.assertEqual(p1, ['LOGIN', 'SirVer', "SUPERUSER"])
        self.assertEqual(p2[0], 'TIME')
        self.assertEqual(p3, ['CLIENTS_UPDATE'])

        self._send(1, "LOGIN", 0, "otto", "build-18", 1, "ottoiscool")
        p1, p2, p3 = self._recv(1)
        self.assertEqual(p1, ['LOGIN', 'otto', "REGISTERED"])
        self.assertEqual(p2[0], 'TIME')
        self.assertEqual(p3, ['CLIENTS_UPDATE'])

        # 0 should get an CLIENTS_UPDATE
        p1, = self._recv(0)
        self.assertEqual(p1, ['CLIENTS_UPDATE'])

    def test_nonanon_login_incorrect_password(self):
        self._send(0, "LOGIN", 0, "SirVer", "build-17", 1, "12345")
        p, = self._recv(0)
        self.assertEqual(p, ['ERROR', 'LOGIN', 'WRONG_PASSWORD'])
# End: Test Login  }}}
# Test Relogin  {{{
class TestRelogin_Anon(_Base, unittest.TestCase):
    def setUp(self):
        _Base.setUp(self)
        self._send(0, "LOGIN", 0, "bert", "build-17", "false")
        self._send(2, "LOGIN", 0, "otto", "build-17", "true", "ottoiscool")
        self._send(3, "LOGIN", 0, "SirVer", "build-17", "true", "123456")
        self._recv(0)
        self._recv(2)
        self._recv(3)

    def test_relogin_ping_and_reply(self):
        self._send(1, "RELOGIN", 0, "bert", "build-17", "false")
        p1, = self._recv(0) # Should have gotten a ping request
        self.assertEqual(p1, ["PING"])

        self._send(0, "PONG")
        self.assertFalse(self._recv(0))

        p1, = self._recv(1)
        self.assertEqual(p1, ["ERROR", "RELOGIN", "CONNECTION_STILL_ALIVE"])

    def test_relogin_ping_and_noreply(self):
        self._send(1, "RELOGIN", 0, "bert", "build-17", "false")
        p1, = self._recv(0)
        self.assertEqual(p1, ["PING"])

        self.clock.advance(6)

        # Connection was terminated for old user
        p1, = self._recv(0)
        self.assertEqual(p1, ["DISCONNECT", "TIMEOUT"])

        # Relogin accepted
        p1, = self._recv(1)
        self.assertEqual(p1, ["RELOGIN"])

    def test_relogin_notloggedin(self):
        self._send(1, "RELOGIN", 0, "iamnotbert", "build-17", "false")
        p1, = self._recv(1)

        self.assertEqual(p1, ["ERROR", "RELOGIN", "NOT_LOGGED_IN"])
        self.assertFalse(self._recv(0))

    def test_relogin_wronginformation_wrong_proto(self):
        self._send(1, "RELOGIN", 1, "bert", "build-17", "false")
        p1, = self._recv(1)
        self.assertEqual(p1, ["ERROR", "RELOGIN", "WRONG_INFORMATION"])
        self.assertFalse(self._recv(0))

    def test_relogin_wronginformation_wrong_buildid(self):
        self._send(1, "RELOGIN", 0, "bert", "uild-17", "false")
        p1, = self._recv(1)
        self.assertEqual(p1, ["ERROR", "RELOGIN", "WRONG_INFORMATION"])
        self.assertFalse(self._recv(0))
    def test_relogin_wronginformation_wrong_loggedin(self):
        self._send(1, "RELOGIN", 0, "bert", "build-17", "true")
        p1, = self._recv(1)
        self.assertEqual(p1, ["ERROR", "RELOGIN", "WRONG_INFORMATION"])
        self.assertFalse(self._recv(0))
    def test_relogin_wronginformation_wrong_loggedin_nonanon(self):
        self._send(1, "RELOGIN", 0, "otto", "build-17", "false")
        p1, = self._recv(1)
        self.assertEqual(p1, ["ERROR", "RELOGIN", "WRONG_INFORMATION"])
        self.assertFalse(self._recv(0))
    def test_relogin_wronginformation_wrong_passwordl(self):
        self._send(1, "RELOGIN", 0, "otto", "build-17", "true", "12345")
        p1, = self._recv(1)
        self.assertEqual(p1, ["ERROR", "RELOGIN", "WRONG_INFORMATION"])

        self.assertFalse(self._recv(0))
    def test_relogin_loggedin_allcorrect(self):
        self._send(1, "RELOGIN", 0, "otto", "build-17", "true", "ottoiscool")
        p1, = self._recv(2)
        self.assertEqual(p1, ["PING"])

        self.clock.advance(6)

        # Connection was terminated for old user
        p1, = self._recv(2)
        self.assertEqual(p1, ["DISCONNECT", "TIMEOUT"])

        # Relogin accepted
        p1, = self._recv(1)
        self.assertEqual(p1, ["RELOGIN"])
# End: Test Relogin  }}}
# Test Chat  {{{
class TestChat(_Base, unittest.TestCase):
    def setUp(self):
        _Base.setUp(self)
        self._send(0, "LOGIN", 0, "bert", "build-17", "false")
        self._send(1, "LOGIN", 1, "ernie", "build-17", "false")
        self._recv(0)
        self._recv(1)

    def test_public_chat(self):
        self._send(0, "CHAT", "hello there", "")
        p0, = self._recv(0)
        p1, = self._recv(1)
        self.assertEqual(p0,p1)
        self.assertEqual(p1, ["CHAT", "bert", "hello there", "false", "false"])

    def test_private_chat(self):
        self._send(0, "CHAT", "hello there", "ernie")
        self.assertEqual([], self._recv(0))
        p1, = self._recv(1)
        self.assertEqual(p1, ["CHAT", "bert", "hello there", "true", "false"])
# End: Test Chat  }}}
# Test Game Creation/Joining  {{{
class TestChat(_Base, unittest.TestCase):
    def setUp(self):
        _Base.setUp(self)
        self._send(0, "LOGIN", 0, "bert", "build-16", "false")
        self._send(1, "LOGIN", 0, "otto", "build-17", "true", "ottoiscool")
        self._send(2, "LOGIN", 0, "SirVer", "build-18", "true", "123456")
        self._recv(0)
        self._recv(1)
        self._recv(2)

    def test_create_game(self):
        self._send(0, "GAME_OPEN", "my cool game", 8)
        p1,p2 = self._mult_receive(range(3))

        self.assertEqual(p1, ["GAMES_UPDATE"])
        self.assertEqual(p2, ["CLIENTS_UPDATE"])

        self._send(1, "CLIENTS")
        p, = self._recv(1)

        self.assertEqual(p, ["CLIENTS", "3",
            "bert", "build-16", "my cool game", "UNREGISTERED", "",
            "otto", "build-17", "", "REGISTERED", "",
            "SirVer", "build-18", "", "SUPERUSER", ""
        ])

    def test_join_game(self):
        self._send(0, "GAME_OPEN", "my cool game", 8)
        p1,p2 = self._mult_receive(range(3))

        self._send(1, "GAME_CONNECT", "my cool game")
        p1, = self._mult_receive(range(3))
        self.assertEqual(p1, ["CLIENTS_UPDATE"])

        # TODO: we should receive something
        self._send(2, "CLIENTS")
        p, = self._recv(2)
        self.assertEqual(p, ["CLIENTS", "3",
            "bert", "build-16", "my cool game", "UNREGISTERED", "",
            "otto", "build-17", "my cool game", "REGISTERED", "",
            "SirVer", "build-18", "", "SUPERUSER", ""
        ])



# TODO: game is full -> can't join
# TODO: joining non existing game
# End: Test Game Creation/Joining  }}}



