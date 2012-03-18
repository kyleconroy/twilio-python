import logging
import os
from twilio import TwilioException
from twilio.rest.resources import make_request
from twilio.rest.resources import Accounts
from twilio.rest.resources import Applications
from twilio.rest.resources import AuthorizedConnectApps
from twilio.rest.resources import Calls
from twilio.rest.resources import CallerIds
from twilio.rest.resources import ConnectApps
from twilio.rest.resources import Notifications
from twilio.rest.resources import Recordings
from twilio.rest.resources import Transcriptions
from twilio.rest.resources import Sms
from twilio.rest.resources import Participants
from twilio.rest.resources import PhoneNumbers
from twilio.rest.resources import Conferences
from twilio.rest.resources import Sandboxes
from urllib import urlencode
from urlparse import urljoin


def find_credentials():
    """
    Look in the current environment for Twilio credentails
    """
    try:
        account = os.environ["TWILIO_ACCOUNT_SID"]
        token = os.environ["TWILIO_AUTH_TOKEN"]
        return account, token
    except KeyError:
        return None, None


class TwilioRestClient(object):
    """
    A client for accessing the Twilio REST API
    """

    def __init__(self, account=None, token=None, base="https://api.twilio.com",
                 version="2010-04-01", client=None):
        """
        Create a Twilio REST API client.
        """

        # Get account credentials
        if not account or not token:
            account, token = find_credentials()
            if not account or not token:
                raise TwilioException("""
Twilio could not find your account credentials. Pass them into the
TwilioRestClient constructor like this:

    client = TwilioRestClient(account='AC38135355602040856210245275870',
                              token='2flnf5tdp7so0lmfdu3d')

Or, add your credentials to your shell environment. From the terminal, run

    echo "export TWILIO_ACCOUNT_SID=AC3813535560204085626521" >> ~/.bashrc
    echo "export TWILIO_AUTH_TOKEN=2flnf5tdp7so0lmfdu3d7wod" >> ~/.bashrc

and be sure to replace the values for the Account SID and auth token with the
values from your Twilio Account at https://www.twilio.com/user/account.
""")
        
        self.base = base
        auth = (account, token)
        version_uri = "%s/%s" % (base, version)
        account_uri = "%s/%s/Accounts/%s" % (base, version, account)

        self.accounts = Accounts(version_uri, auth)
        self.applications = Applications(account_uri, auth)
        self.authorized_connect_apps = AuthorizedConnectApps(account_uri, auth)
        self.calls = Calls(account_uri, auth)
        self.caller_ids = CallerIds(account_uri, auth)
        self.connect_apps = ConnectApps(account_uri, auth)
        self.notifications = Notifications(account_uri, auth)
        self.recordings = Recordings(account_uri, auth)
        self.transcriptions = Transcriptions(account_uri, auth)
        self.sms = Sms(account_uri, auth)
        self.phone_numbers = PhoneNumbers(account_uri, auth)
        self.conferences = Conferences(account_uri, auth)
        self.sandboxes = Sandboxes(account_uri, auth)

        self.auth = auth
        self.account_uri = account_uri

    def participants(self, conference_sid):
        """
        Return a :class:`Participants` instance for the :class:`Conference`
        with the given conference_sid
        """
        base_uri = "%s/Conferences/%s" % (self.account_uri, conference_sid)
        return Participants(base_uri, self.auth)

