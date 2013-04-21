#!/usr/bin/env python


import sys
from cStringIO import StringIO
import datetime
import time
import urllib
import string

from reportlab.lib.units import cm, mm, inch, pica
from reportlab.lib.colors import black, red, grey
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

#creates a 6'x4' pdf containing the 6 images supplied in a 3x2 grid with margin
def buildPDFx6(marginmm, urls):
    width = 6 * inch
    height = 4 * inch
    square = 2 * inch
    margin = marginmm * mm
    card_width = square-(margin * 2)
    buffer = StringIO()
    pdf = Canvas(buffer)
    pdf.setPageSize((width,height))
    def create_image(url):
        for i in [1,2]:
            try:
                return ImageReader(url)
            except IOError:
                pass
        return ImageReader(url)

    def put_image(x,y,url):
      if url != "":
        img = create_image(url)
        pdf.drawImage(img,(square*x)+margin,(square*y)+margin,
              width=card_width, height=card_width)

    put_image(0,1,urls[0])
    put_image(0,0,urls[1])
    put_image(1,1,urls[2])
    put_image(1,0,urls[3])
    put_image(2,1,urls[4])
    put_image(2,0,urls[5])
    pdf.save()
    data = buffer.getvalue()
    buffer.close()
    return data

