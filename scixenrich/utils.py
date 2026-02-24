import json
import sys

import requests
import unidecode
import time


class UnicodeDecodeError(Exception):
    pass


def u2asc(input):
    """
    Converts/transliterates unicode characters to ASCII, using the unidecode package.
    Functionality is similar to the legacy code in adspy.Unicode, but may treat some characters differently
    (e.g. umlauts). Standard unidecode package only handles Latin-based characters.
    :param input: string to be transliterated. Can be either unicode or encoded in utf-8
    :return output: transliterated string, in either unicode or encoded (to match input)
    """

    # TODO If used on anything but author names, add special handling for math symbols and other special chars
    output = None
    if sys.version_info < (3,):
        test_type = unicode
    else:
        test_type = str

    if not isinstance(input, test_type):
        try:
            input = input.decode("utf-8")
        except UnicodeDecodeError:
            raise UnicodeHandlerError("Input must be either unicode or encoded in utf8.")

    try:
        output = unidecode.unidecode(input)
    except UnicodeDecodeError:
        raise UnicodeHandlerError("Transliteration failed, check input.")

    if not isinstance(input, test_type):
        output = output.encode("utf-8")

    return output


def issn2info(token=None, url=None, issn=None, maxtries=1, sleeptime=1, return_info="bibstem"):
    """
    Sends an ISSN to the JournalsDB API and returns the field specified by `return_info`
    Default info to be returned is bibstem
    """
    if issn and token and url:
        url_base = url + "/journals/issn/"
        request_url = url_base + issn
        token_dict = {"Authorization": "Bearer %s" % token}
        icount = 0
        while icount < maxtries:
            try:
                req = requests.get(request_url, headers=token_dict)
            except Exception as err:
                icount += 1
            else:
                if req.status_code == 200:
                    result = req.json()
                    return result.get("issn", {}).get(return_info, None)
                elif req.status_code >= 500:
                    time.sleep(sleeptime)
                    icount += 1
                else:
                    return

def name2bib(token=None, url=None, name=None, maxtries=1, sleeptime=1):
    """
    Sends a journal name to the JournalsDB API and returns the resulting
    list.  It then checks for an exact match, and if found, returns the 
    bibstem.
    """
    if name and token and url:
        url_base = url + "/journals/journal/"
        request_url = url_base + name
        token_dict = {"Authorization": "Bearer %s" % token}
        icount = 0
        while icount < maxtries:
            try:
                req = requests.get(request_url, headers=token_dict)
            except Exception as err:
                icount += 1
            else:
                bibstem = None
                if req.status_code == 200:
                    result = req.json()
                    jlist = result.get("journal", [])
                    if jlist:
                        for j in jlist:
                            if name == j.get("name", None):
                                bibstem = j.get("bibstem", None)
                    return bibstem
                elif req.status_code >= 500:
                    time.sleep(sleeptime)
                    icount += 1
                else:
                    return
