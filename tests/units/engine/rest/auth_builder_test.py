import os
import unittest
from unittest.mock import Mock, patch
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from redant.engine.rest import AuthBuilder, BearerAuth


class LocalAccessToken:
    @classmethod
    def get(cls):
        cls.set()
        return os.environ.get('REDANT_BEARER_ACCESS_TOKEN')

    @classmethod
    def set(cls):
        if not os.environ.get('REDANT_BEARER_ACCESS_TOKEN'):
            os.environ['REDANT_BEARER_ACCESS_TOKEN'] = '!@#$%^&*()1234567890'

    @classmethod
    def clear(cls):
        if os.environ.get('REDANT_BEARER_ACCESS_TOKEN'):
            del os.environ['REDANT_BEARER_ACCESS_TOKEN']


class AuthBuilderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.__basic_args = {
            'auth_type': 'basic',
            'username': Mock(spec=str),
            'password': Mock(spec=str),
        }
        self.__digest_args = {
            'auth_type': 'digest',
            'username': Mock(spec=str),
            'password': Mock(spec=str),
        }
        self.__bearer_args = {
            'auth_type': 'bearer',
            'url': Mock(spec=str),
            'method': Mock(spec=str),
            'headers': Mock(spec=str),
            'body': Mock(spec=str),
            'body_as_json': Mock(spec=dict)
        }
        self.__bearer_auth = AuthBuilder(name=Mock(spec=str), auth_args=self.__bearer_args)

    # checks whether the HTTPBasicAuth class is instantiated with specified username and password
    @patch('redant.engine.rest.HTTPBasicAuth')
    def test_basic_auth_called_HTTPBasicAuth_with_specified_username_and_password(self, HTTPBasicAuthMock):
        AuthBuilder(name=Mock(spec=str), auth_args=self.__basic_args)
        HTTPBasicAuthMock.assert_called_once_with(self.__basic_args['username'], self.__basic_args['password'])

    # checks whether this auth is an instance of HTTPBasicAuth class
    def test_basic_auth_is_instance_of_HTTPBasicAuth(self):
        auth_builder = AuthBuilder(name=Mock(spec=str), auth_args=self.__basic_args)
        self.assertTrue(isinstance(auth_builder.auth, HTTPBasicAuth))

    # checks whether the HTTPDigestAuth class is instantiated with specified username and password
    @patch('redant.engine.rest.HTTPDigestAuth')
    def test_digest_auth_called_HTTPDigestAuth_with_specified_username_and_password(self, HTTPDigestAuthMock):
        AuthBuilder(name=Mock(spec=str), auth_args=self.__digest_args)
        HTTPDigestAuthMock.assert_called_once_with(self.__digest_args['username'], self.__digest_args['password'])

    # checks whether this auth is an instance of HTTPBasicAuth class
    def test_digest_auth_is_instance_of_HTTPDigestAuth(self):
        auth_builder = AuthBuilder(name=Mock(spec=str), auth_args=self.__digest_args)
        self.assertTrue(isinstance(auth_builder.auth, HTTPDigestAuth))

    # checks whether this auth is an instance of BearerAuth class
    def test_bearer_auth_is_instance_of_BearerAuth(self):
        LocalAccessToken.set()
        auth_builder = AuthBuilder(name=Mock(spec=str), auth_args=self.__bearer_args)
        self.assertTrue(isinstance(auth_builder.auth, BearerAuth))

    # checks whether the access token is taken from the local environment variable
    def test_get_access_token_from_local(self):
        LocalAccessToken.set()
        auth_builder = AuthBuilder(name=Mock(spec=str), auth_args=self.__bearer_args)
        access_token = auth_builder.access_token
        self.assertEqual(access_token, LocalAccessToken.get())

    # checks whether the access token is taken from the remote server
    def test_get_access_token_from_remote(self):
        pass
