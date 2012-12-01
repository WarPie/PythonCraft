import os
import base64

EXTENSIONS = [
    '.png',
]

def Write(str, mode):
    f = open("textures.py", mode) 
    try:
        f.write(str)
    finally:
        f.close()

def print_data(data):
    size = 72
    offset = 0
    length = len(data)
    while offset < length:
        print '    "%s"' % data[offset:offset+size]
        offset += size
        
def save_data(data):
    size = 72*2
    offset = 0
    length = len(data)

    Write("TEXTURE_DATA = (\n", "w")
    
    while offset < length:
        Write('    "' + data[offset:offset+size] + '"\n', "a")
        offset += size

    Write(')', "a")
    
def generate(folder):
    print '# Automatically generated file!'
    print 'from wx.lib.embeddedimage import PyEmbeddedImage'
    print
    for name in os.listdir(folder):
        if name[-4:] not in EXTENSIONS:
            continue
        path = os.path.join(folder, name)
        base = name[:-4]
        with open(path, 'rb') as f:
            encoded = base64.b64encode(f.read())
            print '%s = PyEmbeddedImage(' % base
            print_data(encoded)
            print ')'
            print
            
            save_data(encoded)

if __name__ == '__main__':
    generate('.')
