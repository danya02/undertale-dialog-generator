from __future__ import print_function, unicode_literals

from base64 import b64encode
from collections import namedtuple
from cStringIO import StringIO
from tempfile import mkstemp
import os
import time

from flask import Flask, render_template, request, after_this_request, make_response
from PIL import Image, ImageDraw, ImageFont

BLACK, WHITE = (0, 0, 0), (255, 255, 255)

Size = namedtuple('Size', ['x', 'y'])

UPLOAD_FOLDER = 'static/images/boxes'

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

BASIC_UNICODE_SANITIZER = {
    0x2018: '\'',  # LEFT SINGLE QUOTATION MARK
    0x2019: '\'',  # RIGHT SINGLE QUOTATION MARK
    0x201c: '"',   # LEFT DOUBLE QUOTATION MARK
    0x201d: '"',   # RIGHT DOUBLE QUOTATION MARK
    0x00a0: ' ',   # NO-BREAK SPACE
}


def _clean_text(text):
    return text.translate(BASIC_UNICODE_SANITIZER)


def getFontForCharacter(character):
    font_dir = os.path.join(app.root_path, 'static', 'css', 'fonts')
    if character.lower() == 'sans':
        return ImageFont.load(os.path.join(font_dir, 'a skele-ton.pil'))
    elif character.lower() == 'papyrus':
        return ImageFont.load(os.path.join(font_dir, 'NYEH HEH HEH!.pil'))
    else:
        return ImageFont.truetype(os.path.join(font_dir, 'DTM-Mono.otf'), 13)


def dialogBox(portrait, text, fnt):
    orig_size = Size(298, 84)
    # mode = '1' is black and white
    img = Image.new(b'1', orig_size)
    draw = ImageDraw.Draw(img)
    draw.fontmode = b'1'
    draw.rectangle((4, 4, 294, 80), fill=1)
    draw.rectangle((7, 7, 291, 77), fill=0)
    img.paste(portrait, (13, 12))
    for row, line in enumerate(text.split('\n')[:3]):
        print('"{}"'.format(repr(line)), draw.textsize(line, font=fnt))
        draw.text((77, 16 + row * 18), line.decode('ascii'), fill=1, font=fnt)
    return img.resize(Size(orig_size.x * 2, orig_size.y * 2))


@app.route('/submit', methods=['GET'])
def makeDialogBox():
    character = request.args.get('character')
    text = request.args.get('text')
    ip_addr = request.remote_addr
    app.logger.info('Request {}: "{}" from {}'.format(character, text, ip_addr))
    box = dialogBox(
        Image.open(request.args.get('moodImg').lstrip('/')),
        _clean_text(text),
        getFontForCharacter(character)
    )
    stream = StringIO()
    box.save(stream, format='png')

    @after_this_request
    def cleanup(response):
        stream.close()
        return response

    return b64encode(stream.getvalue())


@app.route('/')
def builder():
    response = make_response(render_template('index.html'))
    response.headers['X-Clacks-Overhead'] = 'GNU Terry Pratchett'
    return response


if __name__ == '__main__':
    app.run(debug=True)
