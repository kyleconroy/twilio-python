from collections import namedtuple
import datetime
import requests
import json
import os

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


def param_key(k):
    return camel_case(gt_lt(k))


def twilio_args(data):
    return {param_key(k): param_value(v) for k,v in data.iteritems()}


def twilio_url(auth, name, key=None,
               base="https://api.twilio.com/2010-04-01/Accounts"):
    if key is not None:
        url = "/{}/{}/{}.json".format(auth[0], name.title(), key)
    else:
        url = "/{}/{}.json".format(auth[0], name.title())
    return base + url


def twilio_resource(auth, data):
    if "from" in data:
        data["sender"] = data["from"]
        del data["from"]

    # TODO: Add date parsing

    for subresource in data.get("subresource_uris", {}).iterkeys():
        data[subresource] = ListResource(auth, subresource)

    return data


def api_request(auth, url, params=None, data=None, method="GET", retry=True):
    resp = requests.request(method, url, auth=auth, 
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


def items(auth, name, **kwargs):
    ntuple = None
    data = {"next_page_uri": twilio_url(auth, name)}

    while data.get("next_page_uri", False):
        data = api_request(auth, data["next_page_uri"], params=kwargs)
        for resource in data[name]:
            resource = twilio_resource(auth, resource)

            if ntuple is None:
                ntuple = namedtuple(name[:-1], resource.keys())

            obj = ntuple(**resource)
            yield getattr(obj, "sid", None), obj


def item(auth, name, key):
    return twilio_resource(auth,
                           api_request(auth, twilio_url(auth, name, key)))


class Resource(object):

    def __init__(self, auth, name, key):
        self._auth = auth
        self._name = name
        self._key = key
        self._fetched = False

    def __getattr__(self, attr):
        self.fetch()
        return getattr(self, attr)

    def fetch(self):
        if not self._fetched:
            self.__dict__.update(**item(self._auth, self._name, self._key))

    def delete(self):
        api_request(twilio_url(self._auth, self._name, self._key),
                    method="DELETE")

    def update(self, **kwargs):
        api_request(twilio_url(self._auth, self._name, self._key),
                    method="POST", data=kwargs)


class ListResource(object):

    def __init__(self, auth, name):
        self._auth = auth
        self._name = name

    def __getitem__(self, key):
        return Resource(self._auth, self._name, key)

    def __delitem__(self, key):
        pass

    def __iter__(self):
        return items(self._auth, self.name)

    def values(self, **kwargs):
        for key, value in items(self._auth, self._name, **kwargs):
            yield value

    def keys(self, **kwargs):
        for key, value in items(self._auth, self._name, **kwargs):
            yield key

    def get(self, key, default=None):
        return self[key]


class Client(object):

    def __init__(self, account=None, token=None):
        if account is None or token is None:
            self._auth = find_credentials()
        else:
            self._auth = (account, token)

    def __getattr__(self, key):
        return ListResource(self._auth, key)


