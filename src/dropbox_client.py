#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import logging
import os
import sys

from os.path import exists, join

if sys.version_info[0] < 3:
    input = raw_input

from dropbox import client as dbclient, rest, session as dbsession


log = logging.getLogger(__name__)
# XXX: Fill in your consumer key and secret below
# You can find these at http://www.dropbox.com/developers/apps
APP_KEY = None
APP_SECRET = None


class AuthorizationDenied(Exception):
    pass


def command(login_required=True):
    """A decorator for handling authentication and exceptions."""
    def decorate(f):
        def wrapper(self, *args):
            if login_required and self.api_client is None:
                print("Please 'login' to execute this command.",
                      file=sys.stderr)
                return

            try:
                return f(self, *args)
            except TypeError as e:
                print(e, file=sys.stderr)
            except rest.ErrorResponse as e:
                msg = e.user_error_msg or str(e)
                print('Error: %s' % msg, file=sys.stderr)

        wrapper.__doc__ = f.__doc__
        return wrapper
    return decorate


class DropboxClient(object):

    def __init__(self, app_key, app_secret, name=None,
                 access_type='app_folder', token_file="dropbox_token.txt"):
        self.app_key = app_key
        self.app_secret = app_secret
        self.name = name or self.__class__.__name__.lower()
        self.token_file = token_file
        self.access_type = access_type
        self._init_client()

    def __getattr__(self, name):
        return getattr(self.api_client, name)

    @property
    def authorized(self):
        return self.api_client is not None

    def _init_client(self):
        """Try to initialize dropbox client with auth code from file."""
        access_token = self._read_token()

        if isinstance(access_token, tuple):
            sess = dbsession.DropboxSession(self.app_key, self.app_secret)
            sess.set_token(access_key, access_secret)
            self.api_client = dbclient.DropboxClient(sess)
            log.debug("Loaded OAuth 1 access token.")
        elif access_token:
            self.api_client = dbclient.DropboxClient(access_token)
            log.debug("Loaded OAuth 2 access token")
        else:
            self.api_client = None

    def _read_token(self):
        """Try to read oauth access token and secret (oauth1) from file."""
        try:
            serialized_token = open(self.token_file).read()
            if serialized_token.startswith('oauth1:'):
                return serialized_token[len('oauth1:'):].split(':', 1)
            elif serialized_token.startswith('oauth2:'):
                return serialized_token[len('oauth2:'):]
            else:
                log.warning("Malformed access token in %r.", self.token_file)
        except (IOError, OSError):
            pass # don't worry if it's not there or can't be read

    @command(login_required=False)
    def login(self):
        """Log in to a Dropbox account via OAuth 2"""
        flow = dbclient.DropboxOAuth2FlowNoRedirect(self.app_key,
                                                    self.app_secret)
        authorize_url = flow.start()

        try:
            code = self.get_auth(authorize_url)
        except AuthorizationDenied:
            return

        try:
            access_token, user_id = flow.finish(code)
        except rest.ErrorResponse as e:
            print('Error: %s' % str(e), file=sys.stderr)
            return

        self._write_tokenfile(access_token, oauth_version=2)
        self.api_client = dbclient.DropboxClient(access_token)

    @command(login_required=False)
    def login_oauth1(self):
        """Log in to a Dropbox account via OAuth 1"""
        sess = dbsession.DropboxSession(self.app_key, self.app_secret,
                                        self.access_type)
        request_token = sess.obtain_request_token()
        authorize_url = sess.build_authorize_url(request_token)

        try:
            code = self.get_auth(authorize_url)
        except AuthorizationDenied:
            return

        try:
            access_token = sess.obtain_access_token()
        except rest.ErrorResponse as e:
            self.stdout.write('Error: %s\n' % str(e))
            return

        self._write_tokenfile(access_token, oauth_version=1)
        self.api_client = dbclient.DropboxClient(sess)

    def get_auth(self, authorize_url, oauth_version=2):
        """Prompt user for authorization.

        Can be overwritten by a sub-class.

        This default implementation does the following:

        OAuth 1:

        * Prints instructions to give authorization on the website.
        * Issues a prompt for confirmation to continue.

        OAuth 2:

        * Prints instructions to obtain the authorization code to stdout.
        * Issues a prompt on the console where the user can enter it.

        Raises AuthorizationDenied if the prompt is canceled via Control-C
        or EOF or the user does not enter a code (oauth2) or confirmy with
        y/yes (oauth1).

        """
        import webbrowser

        print("1. Go to: %s" % authorize_url)
        print('2. Click "Allow" (you might have to log in first).')
        webbrowser.open(authorize_url)

        if oauth_version == 1:
            print("3. Confirm with 'y' and ENTER.\n")
            try:
                response = input("Continue (Y/n)? ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                raise AuthorizationDenied
            else:
                if response not in ('y', 'yes'):
                    raise AuthorizationDenied
        else:
            print("3. Copy the authorization code.\n")

            try:
                code = input("Enter the authorization code here (Control-C) "
                             "to cancel): ")
            except (EOFError, KeyboardInterrupt):
                raise AuthorizationDenied
            else:
                if not code:
                    raise AuthorizationDenied
                return code

    def _write_tokenfile(self, access_token, oauth_version=2):
        if exists(self.token_file):
            flags = os.O_WRONLY
        else:
            flags = os.O_WRONLY | os.O_CREAT

        umask_original = os.umask(0)
        try:
            f = os.fdopen(os.open(self.token_file, flags, 0o600), 'w')
            if oauth_version == 1:
                f.write('oauth1:%s:%s' % (label, access_token.key,
                                          access_token.secret))
            else:
                f.write('oauth2:%s' % access_token)

            f.close()
        finally:
            os.umask(umask_original)

    @command()
    def logout(self):
        """log out of the current Dropbox account"""
        self.api_client = None
        os.unlink(self.TOKEN_FILE)
        self.current_path = ''


def main(args=None):
    from os.path import basename
    from pprint import pprint
    from xdg import BaseDirectory

    try:
        config = {}
        exec(compile(open(args[0]).read(), args[0], 'exec'), {}, config)
        APP_KEY = config.get('APP_KEY')
        APP_SECRET = config.get('APP_SECRET')
    except:
        log.exception("Could not read config file.")

    if not APP_KEY or not APP_SECRET:
        sys.exit("You need to set your APP_KEY and APP_SECRET!")

    logging.basicConfig(level=logging.DEBUG)

    name = 'pydodo'
    token_file = join(BaseDirectory.save_data_path(name), 'dropbox_token')

    client = DropboxClient(APP_KEY, APP_SECRET, name, token_file=token_file)
    if not client.authorized:
        client.login()

    if client.authorized:
        print("Login successful!")
        print("\n".join("%s: %s" % i for i in client.account_info().items()))

        with open(__file__, 'rb') as f:
            response = client.put_file(basename(__file__), f)
            print("uploaded:", response)

        metadata = client.metadata('/')
        print("App folder contents:")
        print("--------------------\n")
        pprint(metadata['contents'])


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
