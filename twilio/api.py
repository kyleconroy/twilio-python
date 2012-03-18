from collections import namedtuple
import twilio
import datetime
import requests
import json
import os
import urlparse

AUTH_MESSAGE = """
Twilio could not find your account credentials. Pass them into the
api.Client constructor like this:

    client = api.Client(account='AC38135355602040856210245275870',
                        token='2flnf5tdp7so0lmfdu3d')

Or, add your credentials to your shell environment. From the terminal, run

    echo "export TWILIO_ACCOUNT_SID=AC3813535560204085626521" >> ~/.bashrc
    echo "export TWILIO_AUTH_TOKEN=2flnf5tdp7so0lmfdu3d7wod" >> ~/.bashrc

and be sure to replace the values for the Account SID and auth token with the
values from your Twilio Account at https://www.twilio.com/user/account.
"""


def find_credentials():
    """Look in the current environment for Twilio credentails"""
    try:
        account = os.environ["TWILIO_ACCOUNT_SID"]
        token = os.environ["TWILIO_AUTH_TOKEN"]
        return account, token
    except KeyError:
        return None, None


def ntuple(data):
    return namedtuple("ntuple", data.iterkeys())(**data)


def camel_case(name):
    return ''.join(word.title() for word in name.split("_"))


def gt_lt(name):
    return name.replace(u"__gt", u">").replace(u"__lt", u"<")


def param_value(v):
    if v == True:
        return "true"
    if v == False:
        return "false"
    if isinstance(v, datetime.datetime):
        return str(v.date())
    if isinstance(v, datetime.date):
        return str(v)
    return v


def parse_name(url):
    o = urlparse.urlparse(url)
    path, ext = os.path.splitext(o.path)
    name = os.path.split(path)[1].lower()
    return urlparse.urlunparse([o.scheme, o.netloc, path, "", "", ""]), name


def param_key(k):
    return camel_case(gt_lt(k))


def twilio_args(data):
    return {param_key(k): param_value(v) for k,v in data.iteritems()}


def twilio_resource(auth, data):
    if "from" in data:
        data["sender"] = data["from"]
        del data["from"]

    # TODO: Add date parsing

    for subresource, url in data.get("subresource_uris", {}).iteritems():
        data[subresource] = ListResource(auth, url)

    return data


def api_request(auth, url, params=None, data=None, method="GET", retry=True):
    headers = {
        "User-Agent": "twilio-python/%s" % twilio.__version__,
        "Accept": "application/json",
        }

    resp = requests.request(method, url + ".json", auth=auth, headers=headers,
                            params=twilio_args(params or {}),
                            data=twilio_args(data or {}))
    if resp.ok:
        return json.loads(resp.text)

    if retry and resp.status_code >= 500:
        # Server Error, try again
        return api_request(auth, url, method=method,retry=False)

    try:
        data = json.loads(resp.text)
        error = data["message"]
    except:
        error = False

    if resp.status_code == 404:
        raise KeyError(error or "The resource {} couldn't be found".format(url))

    if resp.status_code == 400:
        raise ValueError(error or "You messed up")

    raise RuntimeError(error or "The Twilio API is sad") 


class Resource(object):

    def __init__(self, auth, url, **kwargs):
        if kwargs: self._load(kwargs)
        self._auth = auth
        self._url, _ = parse_name(url)
        self._loaded = False

    def __getattr__(self, attr):
        self.fetch()
        return getattr(self, attr)

    def _load(self, data):
        self._loaded = True
        self.__dict__.update(**twilio_resource(self._auth, data))

    def fetch(self):
        if not self._loaded:
            self._load(api_request(self._auth, self._url))

    def delete(self):
        api_request(self._auth, self._url, method="DELETE")

    def update(self, **kwargs):
        data = api_request(self._auth, self._url, method="POST", data=kwargs)
        self._load(data)


class Call(Resource):

    def cancel(self):
        """ If this call is queued or ringing, cancel the call.
        Will not affect in-progress calls.
        """
        self.update(status="canceled")

    def hangup(self):
        """ If this call is currently active, hang up the call. If this call is
        scheduled to be made, remove the call from the queue.
        """
        self.update(status="completed")

    def route(self, url, method="POST"):
        """Route this call to another url.

        :param url: A valid URL that returns TwiML.
        :param method: The HTTP method Twilio uses when requesting the URL.
        """
        self.update(url=url, method=method)


class Account(Resource):

    def close(self):
        """Permenently deactivate this account"""
        self.update(status="closed")

    def suspend(self):
        """Temporarily suspend this account"""
        self.update(status="suspended")

    def activate(self):
        """Reactivate this account"""
        self.update(status="active")


class Participant(Resource):

    def mute(self):
        """Mute the participant"""
        self.update(muted=True)

    def unmute(self):
        """Unmute the participant"""
        self.update(muted=False)

    def kick(self):
        """Remove the participant from the given conference"""
        self.delete()


class ListResource(object):

    def resource(self):
        return REGISTRY.get(self._name, Resource)

    def __init__(self, auth, url): 
        self._auth = auth
        self._url, self._name = parse_name(url)

    def __getitem__(self, key):
        return Resource(self._auth, self._url + u"/" + key)

    def __delitem__(self, key):
        Resource(self._auth, self._url + u"/" + key).delete()

    def __iter__(self):
        return self.items(self._auth, self._name)

    def create(self, **kwargs):
        resource_data = api_request(self._auth, self._url, data=kwargs)
        sid = resource_data.get(u"sid", u"")
        url = resource_data.get(u"uri", self._url + u"/" + sid)
        return Resource(self._auth, url, **resource_data)

    def items(self, **kwargs):
        data = {u"next_page_uri": self._url}
        while data.get(u"next_page_uri", False):
            data = api_request(self._auth, data[u"next_page_uri"], params=kwargs)
            for resource_data in data[self._name]:
                sid = resource_data.get(u"sid", u"")
                url = resource_data.get(u"uri", self._url + u"/" + sid)
                resource = Resource(self._auth, url, **resource_data)
                yield sid, resource

    def values(self, **kwargs):
        for key, value in self.items(**kwargs):
            yield value

    def keys(self, **kwargs):
        for key, value in self.items(**kwargs):
            yield key

    def get(self, key, default=None):
        return self[key]


class AvailablePhoneNumbers(ListResource):

    def items(self, type="Local", country="US", **kwargs):
        url = self._url + u"/" + type + u"/" + country
        data = api_request(self._auth, url, params=kwargs)
        for resource_data in data[self._name]:
            yield "", ntuple(resource)

    def search(self, **kwargs):
        return self.items(**kwargs)


class IncomingPhoneNumbers(ListResource):

    def purchase(self, **kwargs):
        return self.create(**kwargs)


class OutgoingCallerIds(ListResource):

    def create(self, **kwargs):
        return ntuple(api_request(self._auth, self._url, data=kwargs))

    def validate(self, **kwargs):
        return self.create(**kwargs)


class Client(object):

    def __init__(self, account=None, token=None,
                 base="https://api.twilio.com"):
        if account is None or token is None:
            account, token = find_credentials()
        if not account or not token:
            raise ValueError(AUTH_MESSAGE)

        self._auth = (account, token)
        self._api_base = base + u"/2010-04-01" 
        self._base = self._api_base + u"/Accounts/" + self._auth[0]

    def __getattr__(self, key):
        name = camel_case(key)
        if name == u"Accounts":
            attr = ListResource(self._auth, self._api_base + u"/" + name)
        elif name == u"Sandbox":
            attr = Resource(self._auth, self._base + u"/" + name)
        elif name == u"Messages":
            attr = ListResource(self._auth, self._base + u"/Sms/" + name)
        else:
            attr = ListResource(self._auth, self._base + u"/" + name)

        setattr(self, key, attr)
        return attr
