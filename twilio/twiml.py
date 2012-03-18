"""
Make sure to check out the TwiML overview and tutorial
"""

try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree


MAN = 'man'
WOMAN = 'woman'

ENGLISH = 'en'
BRITISH = 'en-gb'
SPANISH = 'es'
FRENCH = 'fr'
GERMAN = 'de'

GET = "GET"
POST = "POST"


def _attr(value):
    if isinstance(value, bool):
        return str(value).lower()
    else:
        return str(value)


def create_el(root, name):
    def wrapped(body=None, **kwargs):
        return Element(name, parent=root, body=body, **kwargs)
    return wrapped


def response():
    return Verb("Response")


class Element(object):
    """Twilio basic verb object."""

    def __init__(self, name, parent=None, body=None, **kwargs):
        if "sender" in kwargs:
            kwargs["from"] = kwargs["sender"]
            del kwargs["sender"]

        kwargs = {k: _attr(v) for k,v in kwargs.iteritems() if v is not None}

        if parent is not None:
            self.root = etree.SubElement(parent, name, **kwargs) 
        else:
            self.root = etree.Element(name, **kwargs) 

        if body is not None:
            self.root.text = body

    def __str__(self):
        return self.toxml()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def __getattr__(self, name):
        return create_el(self.root, name.title())

    def toxml(self, xml_declaration=True):
        """
        Return the contents of this verb as an XML string

        :param bool xml_declaration: Include the XML declaration. Defaults to
                                     True
        """
        xml = etree.tostring(self.root).encode("utf-8")

        if xml_declaration:
            return u'<?xml version="1.0" encoding="UTF-8"?>' + xml
        else:
            return xml
