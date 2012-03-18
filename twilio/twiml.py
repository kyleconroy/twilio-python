import xml.etree.ElementTree as etree


def _attr(value):
    if isinstance(value, bool):
        return str(value).lower()
    else:
        return str(value)


def _create_el(root, name):
    def wrapped(body=None, **kwargs):
        return Element(name, parent=root, body=body, **kwargs)
    return wrapped


def response():
    """Create a new TwiML Response

    Returns a "Reponse" Element
    """
    return Element("Response")


class Element(object):
    """Create a XML element

    :param tag: Tag for this element
    :param parent: Parent element (if any)
    :param body: XML body (if any)

    All keyword arguments turn into element attributes
    """

    def __init__(self, tag, parent=None, body=None, **kwargs):
        if "sender" in kwargs:
            kwargs["from"] = kwargs["sender"]
            del kwargs["sender"]

        kwargs = {k: _attr(v) for k,v in kwargs.iteritems() if v is not None}

        if parent is not None:
            self.root = etree.SubElement(parent, tag, **kwargs) 
        else:
            self.root = etree.Element(tag, **kwargs) 

        if body is not None:
            self.root.text = body

    def __str__(self):
        return self.toxml()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def __getattr__(self, name):
        return _create_el(self.root, name.title())

    def toxml(self, xml_declaration=True):
        """Return the contents of this verb as an XML string

        :param bool xml_declaration: Include the XML declaration. Defaults to
                                     True
        """
        xml = etree.tostring(self.root).encode("utf-8")

        if xml_declaration:
            return u'<?xml version="1.0" encoding="UTF-8"?>' + xml
        else:
            return xml
