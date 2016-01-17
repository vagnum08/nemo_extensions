#! /usr/bin/python2 -OOt
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.id3 import ID3, APIC, error
from glob import glob
import sys
import os
def add_cover(filename, albumart):
    audio = MP3(filename, ID3=ID3)
    #try:
        #audio.add_tags()
    #except error:
        #pass
    image_type = 3
    if albumart.endswith('png'):
        mime = 'image/png'
    else:
        mime = 'image/jpeg'
    image_desc = 'front cover'
    with open(albumart, 'rb') as f: 
        image_data = f.read()
    apics = [x for x in audio.tags.keys() if 'APIC' in x]
    print 'Found covers: ', apics
    for i in apics:
        audio.tags.pop(i)
    audio.tags.add(
        APIC(
            encoding=3, # 3 is for utf-8
            mime=mime, # image/jpeg or image/png
            type=image_type, # 3 is for the cover image
            desc=image_desc,
            data=image_data
            )
        )
    audio.save()


if __name__ == '__main__':
    f = sys.argv[1]
    full_path = os.path.abspath(f)
    print full_path
    os.chdir(full_path)
    imgs = glob('*.jpg')
    imgs.extend(glob('*.png'))
    mp3s = glob('*.mp3')
    for mp3 in mp3s:
        if 'cover.jpg' in imgs:
            print 'adding cover to ', mp3
            add_cover(mp3, 'cover.jpg')
        elif 'cover.png' in imgs:
            print 'adding cover to ', mp3
            add_cover(mp3, 'cover.png')
        

