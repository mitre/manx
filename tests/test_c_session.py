"""Tests for the Session class."""

from unittest import mock

from plugins.manx.app.c_session import Session


class TestSession:

    def test_session_creation(self):
        conn = mock.Mock()
        session = Session(id=123, paw='test_paw', connection=conn)
        assert session.id == 123
        assert session.paw == 'test_paw'
        assert session.connection is conn

    def test_unique_property(self):
        conn = mock.Mock()
        session = Session(id=1, paw='abc', connection=conn)
        # unique should be deterministic for the same paw
        assert session.unique == session.unique

    def test_different_paws_different_unique(self):
        conn = mock.Mock()
        s1 = Session(id=1, paw='paw1', connection=conn)
        s2 = Session(id=2, paw='paw2', connection=conn)
        assert s1.unique != s2.unique
