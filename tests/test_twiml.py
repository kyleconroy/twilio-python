# -*- coding: utf-8 -*-
from __future__ import with_statement
import re
import twilio
import sys
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

from twilio import twiml
from twilio.twiml import Response
import xml.etree.ElementTree as ET
from xml_compare import xml_compare
from nose.tools import assert_equals, assert_true

class TwilioTest(unittest.TestCase):

    def strip(self, r):
        return str(r)

    def improperAppend(seld, verb):
        pass

def assert_xml_equals(xml1, xml2):
    print xml1
    print xml2
    assert_true(xml_compare(xml1, xml2))

def test_empty_response():
    r = Response()
    assert_xml_equals(r.root, ET.fromstring('<Response />'))


def test_response_add_attribute():
    r = Response(foo="bar")
    assert_xml_equals(r.root, ET.fromstring('<Response foo="bar" />'))


def test_empty_say():
    r = Response()
    r.say()
    assert_xml_equals(r.root, ET.fromstring('<Response><Say /></Response>'))


def test_say_hello_world():
    r = Response()
    r.say(u"Hello World")
    assert_xml_equals(r.root, ET.fromstring('<Response><Say>Hello World</Say></Response>'))


def test_say_french():
    r = Response()
    r.say(u"nécessaire et d'autres")
    xml = '<Response><Say>n&#233;cessaire et d\'autres</Say></Response>'
    assert_xml_equals(r.root, ET.fromstring(xml))


def test_say_loop():
    """should say hello monkey and loop 3 times"""
    r = Response()
    r.say("Hello Monkey", loop=3)
    xml = '<Response><Say loop="3">Hello Monkey</Say></Response>'
    assert_xml_equals(r.root, ET.fromstring(xml))


def test_say_loop_great_britian():
    r = Response()
    r.say("Hello Monkey", language="en-gb")
    xml = '<Response><Say language="en-gb">Hello Monkey</Say></Response>'
    assert_true(xml_compare(r.root, ET.fromstring(xml)))


def test_say_loop_woman():
    """should say have a woman say hello monkey and loop 3 times"""
    r = Response()
    r.say("Hello Monkey", loop=3, voice=twiml.WOMAN)
    xml = '<Response><Say loop="3" voice="woman">Hello Monkey</Say></Response>'
    assert_true(xml_compare(r.root, ET.fromstring(xml)))


def test_say_add_attribute():
    r = Response()
    r.say(foo="bar")
    xml = '<Response><Say foo="bar" /></Response>'
    assert_true(xml_compare(r.root, ET.fromstring(xml)))


def test_say_add_bool():
    r = Response()
    r.say(foo=True)
    xml = '<Response><Say foo="true" /></Response>'
    assert_true(xml_compare(r.root, ET.fromstring(xml)))


def test_context_manager():

    with Response() as r:
        with r.gather() as g:
            g.say("Hello")

        xml = '<Response><Gather><Say>Hello</Say></Gather></Response>'
        assert_xml_equals(r.root, ET.fromstring(xml))


def test_xml_header():
    r = Response()
    assert_true(str(r).startswith('<?xml version="1.0" encoding="UTF-8"?>'))


def test_xml_string():
    r = Response()
    r.play("")

    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<Response><Play /></Response>')

    assert_xml_equals(ET.fromstring(str(r)), ET.fromstring(xml))
