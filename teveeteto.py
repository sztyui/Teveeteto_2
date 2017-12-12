#!/usr/bin/env python3
# -*- coding=utf-8 -*-
"Egy program ami megeteti a tevedet."

from __future__ import print_function
from robobrowser import RoboBrowser
import re
import notify2
import urllib.parse
from random import randint

__author__ = "Istvan Szilagyi"
__credits__ = ["Istvan Szilagyi"]
__license__ = "GPL"
__version__ = "1.0.2"
__maintainer__ = "Istvan Szilagyi"
__email__ = "6323pityu@citromail.hu"
__status__ = "Production"

def ertesit(msg):
    notify2.init("Teve eteto")
    n = notify2.Notification("Teveeteto", msg, "")
    n.show()


class TeveEteto(object):
    "A teve megeteto osztaly!"
    __teveclub_webcim = "http://teveclub.hu/"
    __myteve_webcim = None
    _browser = RoboBrowser(history=True, parser="lxml")

    def __init__(self, username, password):
        "Bemeneti parameterek:\nusername = <felhasznalonev>\npassword = <jelszo>"
        self._browser.open(self.__teveclub_webcim)
        self._username = username
        self._password = password
        self._login()

    def _login(self):
        "Bejelentkezik a teveclub oldalra."
        form = self._browser.get_form(method="post")
        form["tevenev"] = self._username
        form["pass"] = self._password
        self._browser.submit_form(form)
        if re.search(r'/error.pet', self._browser.url):
            res = urllib.parse.urlparse(self._browser.url)
            raise AttributeError("Hibas bejelentkezes: {}".format(res.query))
        self.__myteve_webcim = self._browser.url

    def __enter__(self, *args, **kwargs):
        "Enter funkcio a with statementhez."
        return self

    def __exit__(self, *args):
        pass

    def _kaja_pia_max(self):
        "Meghatarozza a maximum adhato kaja es pia mennyiseget."
        result_dict = dict()
        browser_select = self._browser.find_all("select")
        for select in browser_select:
            if select["name"] == "kaja":
                result_dict.setdefault("kaja", 0)
                result_dict["kaja"] = str(
                    len([x for x in select if x != '\n']))

            if select["name"] == "pia":
                result_dict.setdefault("pia", 0)
                result_dict["pia"] = str(len([x for x in select if x != '\n']))
        return result_dict

    def etet(self, kaja=None, pia=None):
        "Megeteti a szoban forgo tevet."
        self._browser.open(self.__myteve_webcim)
        try:
            form = self._browser.get_forms(
                {"method": "post", "name": "etet"})[0]
        except IndexError:
            return False, "Ma mar megetetted '{name}'-et!".format(name=self._username)
        ertekek = self._kaja_pia_max()
        if kaja:
            ertekek["kaja"] = str(int(kaja))
        if pia:
            ertekek["pia"] = str(int(pia))
        form["kaja"] = ertekek["kaja"]
        form["pia"] = ertekek["pia"]
        self._browser.submit_form(form)
        return True, "{name} megetetve!".format(name=self._username)
        self._browser.back()

    def _get_url_from_href(self, url_regex):
        "Kiszedi az adott regex szerinti url-t a href-ek kozul."
        links = self._browser.find_all('a', href=True)
        hivatkozo_href = [l["href"]
                          for l in links if re.match(url_regex, l['href'])]
        return urllib.parse.urljoin(self.__teveclub_webcim, hivatkozo_href[0])

    def tanit(self):
        "Tanitgatja a szoban forgo tevet."
        self._browser.open(self.__myteve_webcim)
        tanit_url = self._get_url_from_href(r"/tanit.pet$")
        self._browser.open(tanit_url)
        try:
            self._browser.submit_form(
                self._browser.get_forms(
                    {"method": "post", "name": "tanitb"})[0]
            )
        except IndexError:
            self._browser.back()
            return False, "Ma mar tanitgattad '{name}-et!'".format(name=self._username)
        self._browser.back()
        return True, "{name} tanitgatva!".format(name=self._username)

    def _stat_tipp(self, afrom=0, ato=10):
        "Visszaad egy tippet a statisztika alapjan az egyszam jatekban."
        eredmenyek = self.get_egyszam_eredmenyek()
        max_ordered_arr = [(k, eredmenyek[k]) for k in sorted(eredmenyek, key=eredmenyek.get, reverse=False)]
        if ato > len(max_ordered_arr) or afrom > ato:
            raise IndexError("Tulmentel a tombon!")
        return max_ordered_arr[randint(afrom,ato)][0]

    def egyszam(self, rand=True):
        "Tippel egyet az egyszam jatekon."
        self._browser.open(self.__myteve_webcim)
        egysz_url = self._get_url_from_href(r"/egyszam.pet$")
        self._browser.open(egysz_url)
        try:
            input_form = self._browser.get_forms(
                {'method': 'POST', "name": "egyszam"})[0]
        except IndexError:
            self._browser.back()
            return False, "Ma mar tippeltel '{name}'-el".format(name=self._username)
        if rand:
            tipp = randint(0, 999)
        else:
            tipp = self._stat_tipp(0,5)

        input_form["honnan"].value = tipp
        self._browser.submit_form(input_form)
        self._browser.back()

        return True, "{name} tippelt a kovetkezo szamra: {number}".format(
            name=self._username,
            number=tipp
        )

    def __str__(self, show_password=False):
        "Felüldefinialtam a string metodust!"
        if show_password:
            return "Username: {name}\nPassword: {password}".format(
                name=self._username, password=self._password)
        else:
            return "Username: {name}\nPassword: {password}".format(
                name=self._username, password=len(self._password) * '*')

    def get_egyszam_eredmenyek(self):
        """Leszedi az egyszamjatek archivumbol az eddigi tippeket.\nVisszateresi ertekek:\neredmeny: az\
        eredmeny tombje\nmaximum: csokkeno sorrendbe rendezve"""
        if not re.search(r"/egyszam.pet$", self._browser.url):
            egysz_url = self._get_url_from_href(r"/egyszam.pet$")
            self._browser.open(egysz_url)
        egyszam_archivum = self._get_url_from_href(r"/egyszamarc.pet$")
        self._browser.open(egyszam_archivum)
        table = self._browser.find('table', attrs={"id": "content ize"})
        eredmeny = dict()
        for row in table.find('table').findAll('tr')[1:]:
            col = row.findAll('td')
            if len(col) < 2 and len(col) > 3:
                continue
            if re.match("250 f(.*)l(.*)tt$", col[0].string.strip()):
                continue
            try:
                eredmeny[str(col[0].string.strip())] = int(
                    col[2].string.strip())
            except ValueError:
                continue
        # Feldolgozas befejezve, vissza a kezdolapra.
        self._browser.back()

        # Visszaterunk az eredmennyel.
        return eredmeny

    def _where_am_i(self):
        "Seged funkcio, mely megmutatja, a _browser eppen melyik oldalon all."
        return self._browser.url

def main():
    TEVE = TeveEteto("felhasznalonev", "jelszo")
    try:
        ok = True
        val, m = TEVE.etet()
        if not val: 
            ertesit(m)
            ok = False
        val, m = TEVE.tanit()
        if not val: 
            ertesit(m)
            ok = False
        val, m = TEVE.egyszam(rand=False)
        if not val: 
            ertesit(m)
            ok = False
        if ok:
            ertesit("Gondozgatva!")
    except:
        ertesit("Valami hiba tortent.")   

# Ez a main funkcio, ennyi az egesz! ;)
if __name__ == "__main__":
    main()
