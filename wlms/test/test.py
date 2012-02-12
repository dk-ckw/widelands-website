from twisted.internet import task
from twisted.internet.protocol import connectionDone
from twisted.test import proto_helpers
from twisted.trial import unittest

from wlms import MetaServer
from wlms.protocol import GamePingFactory, NETCMD_METASERVER_PING
from wlms.utils import make_packet
from wlms.db.flatfile import FlatFileDatabase

# Helper classes  {{{
class ClientStringTransport(proto_helpers.StringTransport):
    def __init__(self, ip):
        self.client = [ip]
        proto_helpers.StringTransport.__init__(self)

class _Base(object):
    def setUp(self):
        db = FlatFileDatabase("SirVer\t123456\tSUPERUSER\n" + "otto\tottoiscool\tREGISTERED\n")
        self.ms = MetaServer(db)
        self.clock = task.Clock()
        self._cons = [ self.ms.buildProtocol(None) for i in range(10) ]
        self._trs = [ ClientStringTransport("192.168.0.%i" % i) for i in range(10) ]
        self._gptr = None
        self._gpc = None

        def create_game_pinger(gc, timeout):
            p = GamePingFactory(gc, timeout).buildProtocol(None)
            tr = ClientStringTransport("GamePinger")
            p.makeConnection(tr)
            self._gptr = tr
            self._gpc = p

        for c,tr in zip(self._cons, self._trs):
            c.callLater = self.clock.callLater
            c.seconds = self.clock.seconds
            c.create_game_pinger = create_game_pinger

            c.makeConnection(tr)

    def tearDown(self):
        for idx,c in enumerate(self._cons):
            p = self._recv(idx)
            if p:
                raise RuntimeError("unexpected packet from client %i: %r" % (idx, p))
        for c in self._cons:
            c.transport.loseConnection()
            c.connectionLost(connectionDone)

    def _recv(self, client):
        d = self._trs[client].value()
        self._trs[client].clear()
        rv = []
        while len(d):
            size = (ord(d[0]) << 8) + ord(d[1])
            self.assertTrue(size <= len(d))
            rv.append(d[2:size][:-1].split("\x00"))
            d = d[size:]
        self.clock.advance(1e-5)
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
        self.clock.advance(1e-5)
# End: Helper classes  }}}

# Sending Basics  {{{
class TestBasics(_Base, unittest.TestCase):
    def test_sending_absolute_garbage_too_short(self):
        self._cons[0].dataReceived("\xff")
        self.assertFalse(self._recv(0))
    def test_sending_absolute_garbage(self):
        self._cons[0].dataReceived("\xff\x37lkjdflsjflkjsf")
        self.assertFalse(self._recv(0))
    def test_sending_nonexisting_packet(self):
        self._send(0, "BLUMBAQUATSCH")
        p1, = self._recv(0)
        self.assertEqual(p1, ['ERROR', 'GARBAGE_RECEIVED', "INVALID_CMD"])
    def test_sending_toolittle_arguments_packet(self):
        self._send(0, "LOGIN", "hi")
        p1, = self._recv(0)
        self.assertEqual(p1, ['ERROR', 'LOGIN', "Invalid integer: 'hi'"])

    def test_sendtwopacketsinone(self):
        self._send(0, "LOGIN", 0, "testuser", "build-17", "false")
        self._recv(0)
        self._cons[0].dataReceived("\x00\x0aCLIENTS\x00"*2)
        p1,p2 = self._recv(0)
        self.assertEqual(p1, p2)
        self.assertEqual(p1, ['CLIENTS', '1', 'testuser', 'build-17', '', 'UNREGISTERED', ''])

    def test_fragmented_packages(self):
        self._send(0, "LOGIN", 0, "testuser", "build-17", "false")
        self._recv(0)

        self._cons[0].dataReceived("\x00\x0aCLI")
        self._cons[0].dataReceived("ENTS\x00\x00\x0a")
        p1, = self._recv(0)
        self._cons[0].dataReceived("CLIENTS\x00\x00\x08")
        p2, = self._recv(0)
        self.assertEqual(p1, p2)

        self.assertEqual(p1, ['CLIENTS', '1', 'testuser', 'build-17', '', 'UNREGISTERED', ''])
# End: Sending Basics  }}}
# Test Regular Pinging {{{
class TestRegularPinging(_Base, unittest.TestCase):
    def setUp(self):
        _Base.setUp(self)
        self._send(0, "LOGIN", 0, "bert", "build-17", "false")
        self._recv(0)

    def test_regular_cycle(self):
        self.clock.advance(15) # Don't speak for 15 seconds
        p1, = self._recv(0)  # Expect a ping packet
        self.assertEqual(p1, ["PING"])
        self._send(0, "PONG")

        self.clock.advance(15)
        p1, = self._recv(0)  # Expect a ping packet
        self.assertEqual(p1, ["PING"])
        self._send(0, "PONG")

    def test_stay_quiet(self):
        self.clock.advance(10.5)
        p1, = self._recv(0)  # Expect a ping packet
        self.assertEqual(p1, ["PING"])
        self.clock.advance(10.5)
        p1, = self._recv(0)  # Expect a timout packet
        self.assertEqual(p1, ["DISCONNECT", "TIMEOUT"])

    def test_delay_ping_by_regular_packet(self):
        self.clock.advance(9.9)
        self._send(0, "CHAT", "hello there", "")
        p1, = self._recv(0)
        self.assertEqual(p1, ["CHAT", 'bert', 'hello there', 'public'])

        self.clock.advance(9.9)
        self._send(0, "CHAT", "hello there", "")
        p1, = self._recv(0)
        self.assertEqual(p1, ["CHAT", 'bert', 'hello there', 'public'])

        self.clock.advance(10.1)
        p1, = self._recv(0)  # Expect a ping packet
        self.assertEqual(p1, ["PING"])
# End: Test Regular Pinging }}}

# Test Login  {{{
class TestLogin(_Base, unittest.TestCase):
    def test_loginanon(self):
        self._send(0, "LOGIN", 0, "testuser", "build-17", "false")
        p1,p2,p3 = list(self._recv(0))
        self.assertEqual(p1, ['LOGIN', 'testuser', "UNREGISTERED"])
        self.assertEqual(p2[0], 'TIME')
        self.assertEqual(p3, ['CLIENTS_UPDATE'])

    def test_loginanon_unknown_protocol(self):
        self._send(0, "LOGIN", 10, "testuser", "build-17", "false")
        p1, = self._recv(0)
        self.assertEqual(p1, ['ERROR', 'LOGIN', "UNSUPPORTED_PROTOCOL"])

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
# TestMotd  {{{
class TestMotd(_Base, unittest.TestCase):
    def setUp(self):
        _Base.setUp(self)
        self._send(0, "LOGIN", 0, "bert", "build-17", "false")
        self._send(1, "LOGIN", 0, "otto", "build-17", "true", "ottoiscool")
        self._send(2, "LOGIN", 0, "SirVer", "build-17", "true", "123456")
        self._recv(0)
        self._recv(1)
        self._recv(2)

    def test_setting_motd(self):
        self._send(2, "MOTD", "Schnulz is cool!")

        p1, = self._mult_receive(range(3))
        self.assertEqual(p1, ["CHAT", "", "Schnulz is cool!", "system"])

    def test_login_with_motd_set(self):
        self._send(2, "MOTD", "Schnulz is cool!")
        p1, = self._mult_receive(range(3))

        self._send(4, "LOGIN", 0, "fasel", "build-18", "false")
        p1,p2,p3,p4 = self._recv(4)

        self.assertEqual(p1, ['LOGIN', 'fasel', "UNREGISTERED"])
        self.assertEqual(p2[0], 'TIME')
        self.assertEqual(p3, ['CLIENTS_UPDATE'])
        self.assertEqual(p4, ["CHAT", "", "Schnulz is cool!", "system"])

        p1, = self._mult_receive(range(3))
        self.assertEqual(p1, ["CLIENTS_UPDATE"])


    def test_setting_motd_forbidden(self):
        self._send(1, "MOTD", "Schnulz is cool!")
        self._send(0, "MOTD", "Schnulz is cool!")

        p1, = self._mult_receive([0,1])
        self.assertEqual(p1, ["ERROR", "MOTD", "DEFICIENT_PERMISSION"])
# End: TestMotd  }}}
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
        self._send(1, "LOGIN", 0, "ernie", "build-17", "false")
        self._recv(0)
        self._recv(1)

    def test_public_chat(self):
        self._send(0, "CHAT", "hello there", "")
        p0, = self._mult_receive([0,1])
        self.assertEqual(p0, ["CHAT", "bert", "hello there", "public"])

    def test_sanitize_public_chat(self):
        self._send(0, "CHAT", "hello <rt>there</rt>\nhow<rtdoyoudo", "")
        p0, = self._mult_receive([0,1])
        self.assertEqual(p0, ["CHAT", "bert", "hello &lt;rt>there&lt;/rt>\nhow&lt;rtdoyoudo", "public"])

    def test_private_chat(self):
        self._send(0, "CHAT", "hello there", "ernie")
        self.assertEqual([], self._recv(0))
        p1, = self._recv(1)
        self.assertEqual(p1, ["CHAT", "bert", "hello there", "private"])

    def test_sanitize_private_chat(self):
        self._send(0, "CHAT", "hello <rt>there</rt>\nhow<rtdoyoudo", "ernie")
        self.assertEqual([], self._recv(0))
        p1, = self._recv(1)
        self.assertEqual(p1, ["CHAT", "bert", "hello &lt;rt>there&lt;/rt>\nhow&lt;rtdoyoudo", "private"])

# End: Test Chat  }}}
# Test Game Creation/Joining  {{{
class TestGameCreation(_Base, unittest.TestCase):
    def setUp(self):
        _Base.setUp(self)
        self._send(0, "LOGIN", 0, "bert", "build-16", "false")
        self._send(1, "LOGIN", 0, "otto", "build-17", "true", "ottoiscool")
        self._send(2, "LOGIN", 0, "SirVer", "build-18", "true", "123456")
        self._recv(0)
        self._recv(1)
        self._recv(2)

    def test_create_game_and_ping_reply(self):
        self._send(0, "GAME_OPEN", "my cool game", 8)
        b1,b2 = self._mult_receive(range(3))
        self.assertEqual(b1, ["GAMES_UPDATE"])
        self.assertEqual(b2, ["CLIENTS_UPDATE"])

        self._send(1, "CLIENTS")
        p, = self._recv(1)

        self.assertEqual(p, ["CLIENTS", "3",
            "bert", "build-16", "my cool game", "UNREGISTERED", "",
            "otto", "build-17", "", "REGISTERED", "",
            "SirVer", "build-18", "", "SUPERUSER", ""
        ])

        data = self._gptr.value(); self._gptr.clear()
        self.assertEqual(data, NETCMD_METASERVER_PING)
        self._gpc.dataReceived(NETCMD_METASERVER_PING)

        p1,p2 = self._recv(0)
        self.assertEqual(p1, ["GAME_OPEN"])
        self.assertEqual(p2, ["GAMES_UPDATE"])
        p1, = self._mult_receive([1,2])
        self.assertEqual(p1, ["GAMES_UPDATE"])

        self._send(1, "CLIENTS")
        p, = self._recv(1)

        self.assertEqual(p, ["CLIENTS", "3",
            "bert", "build-16", "my cool game", "UNREGISTERED", "",
            "otto", "build-17", "", "REGISTERED", "",
            "SirVer", "build-18", "", "SUPERUSER", ""
        ])

    def test_create_game_twice_pre_ping(self):
        self._send(0, "GAME_OPEN", "my cool game", 8)
        b1,b2 = self._mult_receive(range(3))

        self._send(1, "GAME_OPEN", "my cool game", 12)
        p1, = self._recv(1)
        self.assertEqual(p1, ["ERROR", "GAME_OPEN", "GAME_EXISTS"])

        data = self._gptr.value(); self._gptr.clear()
        self.assertEqual(data, NETCMD_METASERVER_PING)
        self._gpc.dataReceived(NETCMD_METASERVER_PING)
        self._recv(0)
        self._mult_receive([1,2])

        self._send(2, "CLIENTS")
        p, = self._recv(2)

        self.assertEqual(p, ["CLIENTS", "3",
            "bert", "build-16", "my cool game", "UNREGISTERED", "",
            "otto", "build-17", "", "REGISTERED", "",
            "SirVer", "build-18", "", "SUPERUSER", ""
        ])
    def test_create_game_twice_post_ping(self):
        self._send(0, "GAME_OPEN", "my cool game", 8)
        b1,b2 = self._mult_receive(range(3))

        data = self._gptr.value(); self._gptr.clear()
        self.assertEqual(data, NETCMD_METASERVER_PING)
        self._gpc.dataReceived(NETCMD_METASERVER_PING)
        self._recv(0)
        self._mult_receive([1,2])

        self._send(1, "GAME_OPEN", "my cool game", 12)
        p1, = self._recv(1)
        self.assertEqual(p1, ["ERROR", "GAME_OPEN", "GAME_EXISTS"])

        self._send(2, "CLIENTS")
        p, = self._recv(2)

        self.assertEqual(p, ["CLIENTS", "3",
            "bert", "build-16", "my cool game", "UNREGISTERED", "",
            "otto", "build-17", "", "REGISTERED", "",
            "SirVer", "build-18", "", "SUPERUSER", ""
        ])

    def test_create_game_and_no_first_ping_reply(self):
        self._send(0, "GAME_OPEN", "my cool game", 8)
        b1,b2 = self._mult_receive(range(3))
        self.assertEqual(b1, ["GAMES_UPDATE"])
        self.assertEqual(b2, ["CLIENTS_UPDATE"])

        self.clock.advance(15)
        p1,p2,p3 = self._recv(0)
        self.assertEqual(p1, ["PING"])
        self.assertEqual(p2, ["ERROR", "GAME_OPEN", "TIMEOUT"])
        self.assertEqual(p3, ["GAMES_UPDATE"])

        p1, p2 = self._mult_receive([1,2])
        self.assertEqual(p1, ["PING"])
        self.assertEqual(p2, ["GAMES_UPDATE"])

        self._send(2, "CLIENTS")
        p, = self._recv(2)

        self.assertEqual(p, ["CLIENTS", "3",
            "bert", "build-16", "my cool game", "UNREGISTERED", "",
            "otto", "build-17", "", "REGISTERED", "",
            "SirVer", "build-18", "", "SUPERUSER", ""
        ])

        self._send(2, "GAMES")
        p, = self._recv(2)
        self.assertEqual(p, ["GAMES", "0"])

    def test_create_game_and_no_second_ping_reply(self):
        self._send(0, "GAME_OPEN", "my cool game", 8)
        b1,b2 = self._mult_receive(range(3))
        self.assertEqual(b1, ["GAMES_UPDATE"])
        self.assertEqual(b2, ["CLIENTS_UPDATE"])

        data = self._gptr.value(); self._gptr.clear()
        self.assertEqual(data, NETCMD_METASERVER_PING)
        self._gpc.dataReceived(NETCMD_METASERVER_PING)
        p1,p2 = self._recv(0)
        self.assertEqual(p1, ["GAME_OPEN"])
        self.assertEqual(p2, ["GAMES_UPDATE"])
        p1, = self._mult_receive([1,2])
        self.assertEqual(p1, ["GAMES_UPDATE"])

        self.clock.advance(119)
        p1, = self._mult_receive(range(3))
        self.assertEqual(p1, ["PING"])
        for i in range(3): self._send(i, "PONG")

        data = self._gptr.value(); self._gptr.clear()
        self.assertEqual(data, '')

        self.clock.advance(2)
        data = self._gptr.value(); self._gptr.clear()
        self.assertEqual(data, NETCMD_METASERVER_PING)

        # Now, do not answer ping
        self.clock.advance(118)
        p1, = self._mult_receive(range(3))
        self.assertEqual(p1, ["PING"])
        for i in range(3): self._send(i, "PONG")

        self.clock.advance(3)

        p1, = self._mult_receive(range(3))
        self.assertEqual(p1, ["GAMES_UPDATE"])

        self._send(2, "CLIENTS")
        p, = self._recv(2)

        self.assertEqual(p, ["CLIENTS", "3",
            "bert", "build-16", "my cool game", "UNREGISTERED", "",
            "otto", "build-17", "", "REGISTERED", "",
            "SirVer", "build-18", "", "SUPERUSER", ""
        ])

        self._send(2, "GAMES")
        p, = self._recv(2)
        self.assertEqual(p, ["GAMES", "0"])

    def test_join_game(self):
        self._send(0, "GAME_OPEN", "my cool game", 8)
        self._recv(0)
        p1,p2 = self._mult_receive([1,2])

        self._send(1, "GAME_CONNECT", "my cool game")
        p1,p2 = self._recv(1)
        self.assertEqual(p1, ["GAME_CONNECT", "192.168.0.0"])
        self.assertEqual(p2, ["CLIENTS_UPDATE"])

        p1, = self._mult_receive([0,2])
        self.assertEqual(p1, ["CLIENTS_UPDATE"])

        self._send(2, "CLIENTS")
        p, = self._recv(2)
        self.assertEqual(p, ["CLIENTS", "3",
            "bert", "build-16", "my cool game", "UNREGISTERED", "",
            "otto", "build-17", "my cool game", "REGISTERED", "",
            "SirVer", "build-18", "", "SUPERUSER", ""
        ])

    def test_join_full_game(self):
        self._send(0, "GAME_OPEN", "my cool game", 1)
        self._recv(0)
        p1,p2 = self._mult_receive([1,2])

        self._send(1, "GAME_CONNECT", "my cool game")
        p1, = self._recv(1)
        self.assertEqual(p1, ["ERROR", "GAME_CONNECT", "GAME_FULL"])

        self._send(2, "CLIENTS")
        p, = self._recv(2)
        self.assertEqual(p, ["CLIENTS", "3",
            "bert", "build-16", "my cool game", "UNREGISTERED", "",
            "otto", "build-17", "", "REGISTERED", "",
            "SirVer", "build-18", "", "SUPERUSER", ""
        ])

    def test_non_existing_Game(self):
        self._send(1, "GAME_CONNECT", "my cool game")
        p1, = self._recv(1)
        self.assertEqual(p1, ["ERROR", "GAME_CONNECT", "NO_SUCH_GAME"])

        self._send(2, "CLIENTS")
        p, = self._recv(2)
        self.assertEqual(p, ["CLIENTS", "3",
            "bert", "build-16", "", "UNREGISTERED", "",
            "otto", "build-17", "", "REGISTERED", "",
            "SirVer", "build-18", "", "SUPERUSER", ""
        ])

class TestGameStarting(_Base, unittest.TestCase):
    def setUp(self):
        _Base.setUp(self)
        self._send(0, "LOGIN", 0, "bert", "build-16", "false")
        self._send(1, "LOGIN", 0, "otto", "build-17", "true", "ottoiscool")
        self._send(2, "LOGIN", 0, "SirVer", "build-18", "true", "123456")
        self._send(0, "GAME_OPEN", "my cool game", 8)
        self._send(1, "GAME_CONNECT", "my cool game")
        self._recv(0)
        self._recv(1)
        self._recv(2)

    def test_start_game_without_being_in_one(self):
        self._send(2, "GAME_START")
        p1, = self._recv(2)

        self.assertEqual(p1, ["ERROR", "GARBAGE_RECEIVED", "INVALID_CMD"])

    def test_start_game_not_host(self):
        self._send(1, "GAME_START")
        p1, = self._recv(1)

        self.assertEqual(p1, ["ERROR", "GAME_START", "DEFICIENT_PERMISSION"])

    def test_start_game(self):
        self._send(0, "GAME_START")
        p1,p2 = self._recv(0)
        self.assertEqual(p1, ["GAME_START"])

        p1, = self._mult_receive([1,2])
        self.assertEqual(p1, p2)
        self.assertEqual(p2, ["GAMES_UPDATE"])

class TestGameLeaving(_Base, unittest.TestCase):
    def setUp(self):
        _Base.setUp(self)
        self._send(0, "LOGIN", 0, "bert", "build-16", "false")
        self._send(1, "LOGIN", 0, "otto", "build-17", "true", "ottoiscool")
        self._send(2, "LOGIN", 0, "SirVer", "build-18", "true", "123456")
        self._send(0, "GAME_OPEN", "my cool game", 8)
        self._send(1, "GAME_CONNECT", "my cool game")
        self._recv(0)
        self._recv(1)
        self._recv(2)

    def test_leave_game_nothost(self):
        self._send(1, "GAME_DISCONNECT")
        p1, = self._recv(1)
        self.assertEqual(p1, ["CLIENTS_UPDATE"])

        p1, = self._mult_receive([0,2])
        self.assertEqual(p1, ["CLIENTS_UPDATE"])

        self._send(2, "CLIENTS")
        p, = self._recv(2)
        self.assertEqual(p, ["CLIENTS", "3",
            "bert", "build-16", "my cool game", "UNREGISTERED", "",
            "otto", "build-17", "", "REGISTERED", "",
            "SirVer", "build-18", "", "SUPERUSER", ""
        ])

    def test_leave_game_host(self):
        self._send(0, "GAME_DISCONNECT")
        p1,p2 = self._recv(0)
        self.assertEqual(p1, ["CLIENTS_UPDATE"])
        self.assertEqual(p2, ["GAMES_UPDATE"])

        p1,p2 = self._mult_receive([1,2])
        self.assertEqual(p1, ["CLIENTS_UPDATE"])
        self.assertEqual(p2, ["GAMES_UPDATE"])

        self._send(2, "CLIENTS")
        p, = self._recv(2)
        self.assertEqual(p, ["CLIENTS", "3",
            "bert", "build-16", "", "UNREGISTERED", "",
            "otto", "build-17", "my cool game", "REGISTERED", "",
            "SirVer", "build-18", "", "SUPERUSER", ""
        ])

    def test_leave_not_in_game(self):
        self._send(2, "GAME_DISCONNECT")
        p1,= self._recv(2)
        self.assertEqual(p1, ["ERROR", "GARBAGE_RECEIVED", "INVALID_CMD"])

        self._send(2, "CLIENTS")
        p, = self._recv(2)
        self.assertEqual(p, ["CLIENTS", "3",
            "bert", "build-16", "my cool game", "UNREGISTERED", "",
            "otto", "build-17", "my cool game", "REGISTERED", "",
            "SirVer", "build-18", "", "SUPERUSER", ""
        ])
# End: Test Game Creation/Joining  }}}


