"""Tests to verify the command line interface.

.. spelling::

   cli
"""
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :
import sys

import six
import pytest

from cheroot.cli import (
    Application,
    parse_wsgi_bind_addr,
)


@pytest.mark.parametrize(
    ('raw_bind_addr', 'expected_bind_addr'),
    (
        # tcp/ip
        ('192.168.1.1:80', ('192.168.1.1', 80)),
        # ipv6 ips has to be enclosed in brakets when specified in url form
        ('[::1]:8000', ('::1', 8000)),
        ('localhost:5000', ('localhost', 5000)),
        # this is a valid input, but foo gets discarted
        ('foo@bar:5000', ('bar', 5000)),
        ('foo', ('foo', None)),
        ('123456789', ('123456789', None)),
        # unix sockets
        ('/tmp/cheroot.sock', '/tmp/cheroot.sock'),
        ('/tmp/some-random-file-name', '/tmp/some-random-file-name'),
        # abstract sockets
        ('@cheroot', '\x00cheroot'),
    ),
)
def test_parse_wsgi_bind_addr(raw_bind_addr, expected_bind_addr):
    """Check the parsing of the --bind option.

    Verify some of the supported addresses and the expected return value.
    """
    if parse_wsgi_bind_addr(raw_bind_addr) != expected_bind_addr:
        raise AssertionError


@pytest.fixture
def wsgi_app(monkeypatch):
    """Return a WSGI app stub."""
    class WSGIAppMock:
        """Mock of a wsgi module."""

        def application(self):
            """Empty application method.

            Default method to be called when no specific callable
            is defined in the wsgi application identifier.

            It has an empty body because we are expecting to verify that
            the same method is return no the actual execution of it.
            """

        def main(self):
            """Empty custom method (callable) inside the mocked WSGI app.

            It has an empty body because we are expecting to verify that
            the same method is return no the actual execution of it.
            """
    app = WSGIAppMock()
    # patch sys.modules, to include the an instance of WSGIAppMock
    # under a specific namespace
    if six.PY2:
        # python2 requires the previous namespaces to be part of sys.modules
        #   (e.g. for 'a.b.c' we need to insert 'a', 'a.b' and 'a.b.c')
        # otherwise it fails, we're setting the same instance on each level,
        # we don't really care about those, just the last one.
        monkeypatch.setitem(sys.modules, 'mypkg', app)
    monkeypatch.setitem(sys.modules, 'mypkg.wsgi', app)
    return app


@pytest.mark.parametrize(
    ('app_name', 'app_method'),
    (
        (None, 'application'),
        ('application', 'application'),
        ('main', 'main'),
    ),
)
def test_Aplication_resolve(app_name, app_method, wsgi_app):
    """Check the wsgi application name conversion."""
    if app_name is None:
        wsgi_app_spec = 'mypkg.wsgi'
    else:
        wsgi_app_spec = 'mypkg.wsgi:{app_name}'.format(**locals())
    expected_app = getattr(wsgi_app, app_method)
    if Application.resolve(wsgi_app_spec).wsgi_app != expected_app:
        raise AssertionError
