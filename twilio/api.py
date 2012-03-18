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
        api_request(self._auth, self._url, method="POST", data=kwargs)


# Custom cla
class AvailablePhoneNumbers:

    def list(self, type="local", country="US"):
        pass


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
        if name == "Accounts":
            attr = ListResource(self._auth, self._api_base + u"/" + name)
        elif name == "Sandbox":
            attr = Resource(self._auth, self._base + u"/" + name)
        else:
            attr = ListResource(self._auth, self._base + u"/" + name)

        setattr(self, key, attr)
        return attr
