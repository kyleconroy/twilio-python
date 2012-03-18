# -*- coding: utf-8 -*-
from __future__ import with_statement
from twilio import twiml
from twilio.twiml import response
import xml.etree.ElementTree as ET
from xml_compare import xml_compare
from nose.tools import assert_equals, assert_true


def assert_xml_equals(xml1, xml2):
    print xml1
    print xml2
    assert_true(xml_compare(xml1, xml2))


def test_empty_reponse():
    r = reponse()
    assert_xml_equals(r.root, ET.fromstring('<reponse />'))


def test_reponse_add_attribute():
    r = reponse(foo="bar")
    assert_xml_equals(r.root, ET.fromstring('<reponse foo="bar" />'))


def test_empty_say():
    r = reponse()
    r.say()
    assert_xml_equals(r.root, ET.fromstring('<reponse><Say /></reponse>'))


def test_say_hello_world():
    r = reponse()
    r.say(u"Hello World")
    assert_xml_equals(r.root, ET.fromstring('<reponse><Say>Hello World</Say></reponse>'))


def test_say_french():
    r = reponse()
    r.say(u"nécessaire et d'autres")
    xml = '<reponse><Say>n&#233;cessaire et d\'autres</Say></reponse>'
    assert_xml_equals(r.root, ET.fromstring(xml))


def test_say_loop():
    """should say hello monkey and loop 3 times"""
    r = reponse()
    r.say("Hello Monkey", loop=3)
    xml = '<reponse><Say loop="3">Hello Monkey</Say></reponse>'
    assert_xml_equals(r.root, ET.fromstring(xml))


def test_say_loop_great_britian():
    r = reponse()
    r.say("Hello Monkey", language="en-gb")
    xml = '<reponse><Say language="en-gb">Hello Monkey</Say></reponse>'
    assert_true(xml_compare(r.root, ET.fromstring(xml)))


def test_say_loop_woman():
    """should say have a woman say hello monkey and loop 3 times"""
    r = reponse()
    r.say("Hello Monkey", loop=3, voice=twiml.WOMAN)
    xml = '<reponse><Say loop="3" voice="woman">Hello Monkey</Say></reponse>'
    assert_true(xml_compare(r.root, ET.fromstring(xml)))


def test_say_add_attribute():
    r = reponse()
    r.say(foo="bar")
    xml = '<reponse><Say foo="bar" /></reponse>'
    assert_true(xml_compare(r.root, ET.fromstring(xml)))


def test_say_add_bool():
    r = reponse()
    r.say(foo=True)
    xml = '<reponse><Say foo="true" /></reponse>'
    assert_true(xml_compare(r.root, ET.fromstring(xml)))


def test_context_manager():

    with reponse() as r:
        with r.gather() as g:
            g.say("Hello")

        xml = '<reponse><Gather><Say>Hello</Say></Gather></reponse>'
        assert_xml_equals(r.root, ET.fromstring(xml))


def test_xml_header():
    r = reponse()
    assert_true(str(r).startswith('<?xml version="1.0" encoding="UTF-8"?>'))


def test_xml_string():
    r = reponse()
    r.play("")

    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<reponse><Play /></reponse>')

    assert_xml_equals(ET.fromstring(str(r)), ET.fromstring(xml))
