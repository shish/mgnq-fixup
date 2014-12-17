#! /usr/bin/env python

from glob import glob
import sys
import os
import zipfile
import re
from StringIO import StringIO

from lxml import etree
import Image, ImageDraw


def remove_spaces(data):
    # Spaces need to be consistent with splits and the TOC.
    # "Foo Bar.htm" and "Foo%20Bar.htm" are seen as different.

    def fnsan(fn):
        return fn.replace(" ", "").replace("%20", "")

    # rename actual files
    for file_name in data:
        if file_name.endswith(".htm") and file_name != fnsan(file_name):
            data[fnsan(file_name)] = data[file_name]
            del data[file_name]

    # update TOC
    file_name = "toc.ncx"
    root = etree.fromstring(data[file_name])
    for element in root.findall('.//*'):
        if element.get("src"):
            element.set("src", fnsan(element.get("src")))
    data[file_name] = "<?xml version='1.0' encoding='utf-8'?>\n" + etree.tostring(root)

    # update inventory
    file_name = "content.opf"
    root = etree.fromstring(data[file_name])
    for element in root.findall('.//*'):
        if element.get("href"):
            element.set("href", fnsan(element.get("href")))
    data[file_name] = "<?xml version='1.0' encoding='utf-8'?>\n" + etree.tostring(root)


def shorten_title(data):
    #
    # "Magical Girl Noir Quest - Book X" is too long for the bookshelf...
    # It shows up as "Magical Girl Noir Qu..." with no way to tell the
    # difference between Book 1 / 2 / 3
    #
    data["content.opf"] = data["content.opf"].replace("Magical Girl Noir Quest -", "MGNQ")
    data["content.opf"] = data["content.opf"].replace("Magical Girl Noir Quest", "MGNQ")
    data["toc.ncx"] = data["toc.ncx"].replace("Magical Girl Noir Quest -", "MGNQ")
    data["toc.ncx"] = data["toc.ncx"].replace("Magical Girl Noir Quest", "MGNQ")


def thread_title(data):
    #
    # Thread titles in the TOC are wonky.
    # They are just eg "Thread 20:" rather than "Thread 20: Midori III", because the
    # HTML is "<h1>Thread 20:</h1> <p><b>Midori III</b></p>"
    #

    titles = {}

    # figure out the full title for each file name
    for file_name in data:
        if file_name.endswith(".htm"):
            root = etree.fromstring(data[file_name])
            h1 = root.find('.//{http://www.w3.org/1999/xhtml}h1')
            b = root.find('.//{http://www.w3.org/1999/xhtml}b')
            if h1 is not None and h1.text and b is not None and b.text:
                titles[file_name] = h1.text + " " + b.text

    # update toc
    file_name = "toc.ncx"
    root = etree.fromstring(data[file_name])
    for element in root.findall('.//{http://www.daisy.org/z3986/2005/ncx/}navPoint'):
        fn = element[1].get("src")
        if fn in titles:
            element[0][0].text = titles[fn]
    data[file_name] = "<?xml version='1.0' encoding='utf-8'?>\n" + etree.tostring(root)


def fix_speech(data):
    #
    # Android ebook reader's voice synth treats
    #
    #    <p>Once upon a
    #    time there was
    #    a cat</p>
    #
    # as three separate sentences ~_~
    #
    # So, replace all the newline characters with spaces...
    #
    # Also, it thinks "foo...bar" is "foo dot dot dot bar", not "foo <pause> bar"
    #

    for file_name in data:
        if file_name.endswith(".htm"):
            root = etree.fromstring(data[file_name])
            for element in root.findall('.//*'):
                if element.text and element.text.strip():
                    element.text = element.text.replace("\n", " ")
                    element.text = re.sub("([a-zA-Z0-9])(\.{3,})([a-zA-Z0-9])", "\\1\\2 \\3", element.text)

            data[file_name] = etree.tostring(root)


def set_cover_page(data):
    pix = Image.open("cover.jpg")

    # number circle
    draw = ImageDraw.Draw(pix)
    draw.ellipse((300, 150, 400, 250), fill="black")
    draw.ellipse((310, 160, 390, 240), fill="white")

    # numbers
    numbers = Image.open("numbers.png")
    nw, nh = numbers.size  # number width, height
    dw, dh = nw/10, nh  # digit width, height
    n = int(re.search("MGNQ Book ([0-9]+)", data["toc.ncx"]).group(1))
    digit = numbers.crop((n * dw, 0, (n+1)*dw, dh))
    pix.paste(digit, (350-dw/2, 200-dh/2, 350+(dw-dw/2), 200+(dh-dh/2)))

    output = StringIO()
    pix.save(output, format="JPEG")
    data["cover-fixup.jpg"] = output.getvalue()
    output.close()

    # add to content list
    file_name = "content.opf"
    root = etree.fromstring(data[file_name])
    for element in root.findall('.//*'):
        if element.get("id") == "cover":
            element.set("href", "cover-fixup.jpg")
    data[file_name] = etree.tostring(root)

    # set dimentions in title page
    file_name = "titlepage.xhtml"
    root = etree.fromstring(data[file_name])
    for element in root.findall('.//{http://www.w3.org/2000/svg}svg'):
        element.set("viewBox", "0 0 %d %d" % pix.size)
    for element in root.findall('.//{http://www.w3.org/2000/svg}image'):
        element.set("width", str(pix.size[0]))
        element.set("height", str(pix.size[1]))
        element.set("{http://www.w3.org/1999/xlink}href", "cover-fixup.jpg")
    data[file_name] = etree.tostring(root)



if __name__ == "__main__":
    data = {}

    zf = zipfile.ZipFile(sys.argv[1], "r")
    for name in zf.namelist():
        data[name] = zf.read(name)
    zf.close()

    remove_spaces(data)
    shorten_title(data)
    thread_title(data)
    fix_speech(data)
    set_cover_page(data)

    zf = zipfile.ZipFile(sys.argv[2], "w")
    for name in data:
        zf.writestr(name, data[name])
    zf.close()
