from pyglet.gl import *
from pyglet.window import key
from random import randint as randx
import StringIO
import base64
import math
import random
import time
import textures

SECTOR_SIZE = 16

def SaveWorld(world, mode="w"):
    print world
    #f = open("world.py", mode) 
    #try:
        #f.write(world)
    #finally:
        #f.close()

def cube_vertices(x, y, z, n):
    return [
        x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n, # top
        x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n, # bottom
        x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n, # left
        x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n, # right
        x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n, # front
        x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n, # back
    ]

def tex_coord(x, y, n=4):
    m = 1.0 / n
    dx = x * m
    dy = y * m
    return dx, dy, dx + m, dy, dx + m, dy + m, dx, dy + m

def tex_coords(top, bottom, side):
    top = tex_coord(*top)
    bottom = tex_coord(*bottom)
    side = tex_coord(*side)
    result = []
    result.extend(top)
    result.extend(bottom)
    result.extend(side * 4)
    return result

#top, bottom, side
GRASS = tex_coords((1, 0), (0, 1), (0, 0))
SAND = tex_coords((1, 1), (1, 1), (1, 1))
BRICK = tex_coords((2, 0), (2, 0), (2, 0))
STONE = tex_coords((2, 1), (2, 1), (2, 1))
DIRT = tex_coords((0, 1), (0, 1), (0, 1))
BIRCH = tex_coords((0, 3), (0, 3), (1, 3))
MAPLE = tex_coords((0, 2), (0, 2), (1, 2))

PLANK = tex_coords((3, 1), (3, 1), (3, 1))
PLANK_PINE = tex_coords((3, 0), (3, 0), (3, 0))

GRAVEL = tex_coords((3, 2), (3, 2), (3, 2))
FINE_STONE = tex_coords((3, 3), (3, 3), (3, 3))


BIRCH_LEAF = tex_coords((2, 3), (2, 3), (2, 3))
MAPLE_LEAF = tex_coords((2, 2), (2, 2), (2, 2))



FACES = [
    ( 0, 1, 0),
    ( 0,-1, 0),
    (-1, 0, 0),
    ( 1, 0, 0),
    ( 0, 0, 1),
    ( 0, 0,-1),
]

blocks = [GRASS, SAND, BRICK, STONE, FINE_STONE, DIRT, GRAVEL, PLANK, PLANK_PINE, BIRCH, BIRCH_LEAF, MAPLE, MAPLE_LEAF]
current = { "block":0 }

class TextureGroup(pyglet.graphics.Group):

    def __init__(self, data):
        super(TextureGroup, self).__init__()
        fp = StringIO.StringIO(base64.b64decode(data))
        self.texture = pyglet.image.load('__file__.png', file=fp).get_texture()
        
    def set_state(self):
        glEnable(self.texture.target)
        glBindTexture(self.texture.target, self.texture.id)
        
    def unset_state(self):
        glDisable(self.texture.target)

        
        
def normalize(position):
    x, y, z = position
    x, y, z = (int(round(x)), int(round(y)), int(round(z)))
    return (x, y, z)

def sectorize(position):
    x, y, z = normalize(position)
    x, y, z = x / SECTOR_SIZE, y / SECTOR_SIZE, z / SECTOR_SIZE
    return (x, 0, z)

    
    
class Model(object):
    def __init__(self):
        self.batch = pyglet.graphics.Batch()
        self.group = TextureGroup(TEXTURE_DATA)
        self.world = {}
        self.shown = {}
        self._shown = {}
        self.sectors = {}
        self.queue = []
        self.initialize()

    def is_mass(self, position):
        x, y, z = position
        key = normalize((x, y, z))
        if key in self.world:
            return key
        return False
        
    def initialize(self):
        n = 70
        s = 1
        y = 0
        for x in xrange(-n, n + 1, s):
            for z in xrange(-n, n + 1, s):
                self.init_block((x, y - 10, z), STONE)
                if x in (-n, n) or z in (-n, n):
                    for dy in xrange(-2, 3):
                        self.init_block((x, y + dy, z), STONE)
        # Add a ground                
        for y in xrange(-9, -1, s):           
            for x in xrange(-n,n+1, s):
                for z in xrange(-n,n+1, s): 
                    if y >= -2: self.init_block((x, y, z), GRASS)
                    elif y >= randx(-6,-2): self.init_block((x, y, z), GRASS)
                    else: self.init_block((x, y, z), DIRT)
                    
        o = n - random.randint(-3,10)
        v = n - random.randint(-6,12)
        l = n - random.randint(-4,10)
        # Add some blocksets
        for _ in xrange(50):
            a = random.randint(-o, o)
            b = random.randint(-o, o)
            c = -1
            if randx(0,8) == 1:
                h = random.randint(4, 19)
                s = random.randint(2, 18)
            else:
                h = random.randint(1, 5)
                s = random.randint(2, 8)
            d = 1
            t = random.choice([DIRT, GRASS, SAND, GRAVEL])
            for y in xrange(c, c + h):
                for x in xrange(a - s, a + s + 1):
                    for z in xrange(b - s, b + s + 1):
                        if (x - a) ** 2 + (z - b) ** 2 > (s + 1) ** 2:
                            continue
                        if (x - 0) ** 2 + (z - 0) ** 2 < 5 ** 2:
                            continue
                        if h<random.randint(1, 3): 
                            self.init_block((x, y, z), GRASS)
                        elif random.randint(1,30) !=1: 
                            self.init_block((x, y, z), t)
                        if h==random.randint(4,15): 
                            block = self.is_mass((x, y, z))
                            if block: self.remove_block((x, y, z))
                            
                if random.randint(1,2) == 1: s -= d
                if random.randint(1,17) == 1: s += d
                
        # remove some areas (for randomness)       
        for _ in xrange(40):
            a = random.randint(-v, v)
            b = random.randint(-v, v)
            c = random.randint(-8, 5)
            h = random.randint(8, 10)
            s = random.randint(2, 6)
            j = random.randint(2, 15)
            d = 1
            for y in xrange(c, c + h):
                for x in xrange(a - s, a + s + j):
                    for z in xrange(b - s, c + s + 1):
                        if (x - a) ** 2 + (z - b) ** 2 > (s + 1) ** 2:
                            continue
                        if (x - 0) ** 2 + (z - 0) ** 2 < 5 ** 2:
                            continue
                        block = self.is_mass((x, y, z))
                        if block:
                            self.remove_block((x, y, z))
                            
                if random.randint(1,7) == 1: s -= d
                if random.randint(1,2) == 1: s += d
        
        for _ in xrange(80):
            tree = random.choice([MAPLE, MAPLE, MAPLE, BIRCH])
            if tree == BIRCH: leaf = BIRCH_LEAF
            elif tree == MAPLE: leaf = MAPLE_LEAF
            
            zj = random.randint(-l, l+1)
            xj = random.randint(-l, l+1)
            #xj = random.randint(2, 70)
            #zj = random.randint(2, 50)  
            block_is_under = self.is_mass((xj, -2, zj))
            block_in_way = self.is_mass((xj, 1, zj))
            if not block_in_way and block_is_under:
                self.init_block((xj, -1, zj), tree)
                max_h = randx(3,6)
                for h in xrange(0, max_h):
                    self.init_block((xj, h, zj), tree)
                    
                if tree != BIRCH:
                    self.init_block((xj, h, zj+1), leaf)
                    self.init_block((xj, h, zj-1), leaf)
                    self.init_block((xj+1, h, zj), leaf)
                    self.init_block((xj-1, h, zj), leaf)
                
                for y in xrange(2):
                    for x in xrange(-2,3):
                        for z in xrange(-2,3):
                            if z==-2 and x==-2: pass
                            elif z==2 and x==2: pass
                            elif z==2 and x==-2: pass
                            elif z==-2 and x==2: pass
                            else:self.init_block((xj+x, h+y+1, zj+z), leaf)
                
                if randx(1,6)==1:
                    self.init_block((xj, h+3, zj+1), leaf)
                    self.init_block((xj, h+3, zj-1), leaf)
                    self.init_block((xj+1, h+3, zj), leaf)
                    self.init_block((xj-1, h+3, zj), leaf)
                    
                    self.init_block((xj+1, h+3, zj-1), leaf)
                    self.init_block((xj-1, h+3, zj+1), leaf)
                    self.init_block((xj+1, h+3, zj+1), leaf)
                    self.init_block((xj-1, h+3, zj-1), leaf)
                    
                    self.init_block((xj, h+4, zj+1), leaf)
                    self.init_block((xj, h+4, zj-1), leaf)
                    self.init_block((xj+1, h+4, zj), leaf)
                    self.init_block((xj-1, h+4, zj), leaf)
                    self.init_block((xj, h+5, zj), leaf)
                else:
                    self.init_block((xj, h+3, zj+1), leaf)
                    self.init_block((xj, h+3, zj-1), leaf)
                    self.init_block((xj+1, h+3, zj), leaf)
                    self.init_block((xj-1, h+3, zj), leaf)
                    self.init_block((xj, h+4, zj), leaf)
        
    def hit_test(self, position, vector, max_distance=6):
        m = 8
        x, y, z = position
        dx, dy, dz = vector
        previous = None
        for _ in xrange(max_distance * m):
            key = normalize((x, y, z))
            if key != previous and key in self.world:
                return key, previous
            previous = key
            x, y, z = x + dx / m, y + dy / m, z + dz / m
        return None, None
        
    def exposed(self, position):
        x, y, z = position
        for dx, dy, dz in FACES:
            if (x + dx, y + dy, z + dz) not in self.world:
                return True
        return False
        
    def init_block(self, position, texture):
        self.add_block(position, texture, False)
        
    def add_block(self, position, texture, sync=True):
        if position in self.world:
            self.remove_block(position, sync)
        self.world[position] = texture
        self.sectors.setdefault(sectorize(position), []).append(position)
        if sync:
            if self.exposed(position):
                self.show_block(position)
            self.check_neighbors(position)
            
    def remove_block(self, position, sync=True):
        del self.world[position]
        self.sectors[sectorize(position)].remove(position)
        if sync:
            if position in self.shown:
                self.hide_block(position)
            self.check_neighbors(position)
            
    def check_neighbors(self, position):
        x, y, z = position
        for dx, dy, dz in FACES:
            key = (x + dx, y + dy, z + dz)
            if key not in self.world:
                continue
            if self.exposed(key):
                if key not in self.shown:
                    self.show_block(key)
            else:
                if key in self.shown:
                    self.hide_block(key)
    def show_blocks(self):
        for position in self.world:
            if position not in self.shown and self.exposed(position):
                self.show_block(position)
                
    def show_block(self, position, immediate=True):
        texture = self.world[position]
        self.shown[position] = texture
        if immediate:
            self._show_block(position, texture)
        else:
            self.enqueue(self._show_block, position, texture)
            
    def _show_block(self, position, texture):
        x, y, z = position
        # only show exposed faces
        index = 0
        count = 24
        vertex_data = cube_vertices(x, y, z, 0.5)
        texture_data = list(texture)
        for dx, dy, dz in []:#FACES:
            if (x + dx, y + dy, z + dz) in self.world:
                count -= 4
                i = index * 12
                j = index * 8
                del vertex_data[i:i + 12]
                del texture_data[j:j + 8]
            else:
                index += 1
        # create vertex list
        self._shown[position] = self.batch.add(count, GL_QUADS, self.group, 
            ('v3f/static', vertex_data),
            ('t2f/static', texture_data))
            
    def hide_block(self, position, immediate=True):
        self.shown.pop(position)
        if immediate:
            self._hide_block(position)
        else:
            self.enqueue(self._hide_block, position)
            
    def _hide_block(self, position):
        self._shown.pop(position).delete()
        
    def show_sector(self, sector):
        for position in self.sectors.get(sector, []):
            if position not in self.shown and self.exposed(position):
                self.show_block(position, False)
                
    def hide_sector(self, sector):
        for position in self.sectors.get(sector, []):
            if position in self.shown:
                self.hide_block(position, False)
                
    def change_sectors(self, before, after):
        before_set = set()
        after_set = set()
        pad = 4
        for dx in xrange(-pad, pad + 1):
            for dy in [0]: # xrange(-pad, pad + 1):
                for dz in xrange(-pad, pad + 1):
                    if dx ** 2 + dy ** 2 + dz ** 2 > (pad + 1) ** 2:
                        continue
                    if before:
                        x, y, z = before
                        before_set.add((x + dx, y + dy, z + dz))
                    if after:
                        x, y, z = after
                        after_set.add((x + dx, y + dy, z + dz))
        show = after_set - before_set
        hide = before_set - after_set
        for sector in show:
            self.show_sector(sector)
        for sector in hide:
            self.hide_sector(sector)
            
    def enqueue(self, func, *args):
        self.queue.append((func, args))
        
    def dequeue(self):
        func, args = self.queue.pop(0)
        
        func(*args)
    def process_queue(self):
        start = time.clock()
        while self.queue and time.clock() - start < 1 / 60.0:
            self.dequeue()
            
    def process_entire_queue(self):
        while self.queue:
            self.dequeue()

class Window(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.exclusive = False
        self.flying = False
        self.jumping = 0
        self.strafe = [0, 0]
        self.position = (0, 0, 0)
        self.rotation = (0, 0)
        self.sector = None
        self.reticle = None
        self.dy = 0
        self.model = Model()
        
        self.label = pyglet.text.Label('', font_name='Arial', font_size=18, 
            x=10, y=self.height - 10, anchor_x='left', anchor_y='top', 
            color=(0, 0, 0, 255))
        pyglet.clock.schedule_interval(self.update, 1.0 / 60)
        
    def set_exclusive_mouse(self, exclusive):
        super(Window, self).set_exclusive_mouse(exclusive)
        self.exclusive = exclusive
        
    def get_sight_vector(self):
        x, y = self.rotation
        m = math.cos(math.radians(y))
        dy = math.sin(math.radians(y))
        dx = math.cos(math.radians(x - 90)) * m
        dz = math.sin(math.radians(x - 90)) * m
        return (dx, dy, dz)
        
    def get_motion_vector(self):
        if any(self.strafe):
            x, y = self.rotation
            strafe = math.degrees(math.atan2(*self.strafe))
            if self.flying:
                m = math.cos(math.radians(y))
                dy = math.sin(math.radians(y))
                if self.strafe[1]:
                    dy = 0.0
                    m = 1
                if self.strafe[0] > 0:
                    dy *= -1
                dx = math.cos(math.radians(x + strafe)) * m
                dz = math.sin(math.radians(x + strafe)) * m
            else:
                dy = 0.0
                dx = math.cos(math.radians(x + strafe))
                dz = math.sin(math.radians(x + strafe))
        else:
            dy = 0.0
            dx = 0.0
            dz = 0.0
        return (dx, dy, dz)
        
    def update(self, dt):
        self.model.process_queue()
        sector = sectorize(self.position)
        if sector != self.sector:
            self.model.change_sectors(self.sector, sector)
            if self.sector is None:
                self.model.process_entire_queue()
            self.sector = sector
        m = 8
        dt = min(dt, 0.2)
        for _ in xrange(m):
            self._update(dt / m)

    def _update(self, dt):
        # walking
        if self.flying: speed = 12
        else: speed = 5
                    
        d = dt * speed
        dx, dy, dz = self.get_motion_vector()
        dx, dy, dz = dx * d, dy * d, dz * d
        
        #jumping
        if self.dy == 0 and self.jumping >= 2: self.jumping = 0
        
        # gravity
        if not self.flying:
            self.dy -= dt / 5
            self.dy = max(self.dy, -0.5)
            dy += self.dy
            
        # collisions
        x, y, z = self.position
        x, y, z = self.collide((x + dx, y + dy, z + dz), 2)
        self.position = (x, y, z)
        
    def change_block(self, value):
        block = blocks[current['block']]
        current['block'] += value
        
        if current['block']>=len(blocks): current['block'] = 0
        elif current['block']<0: current['block'] = len(blocks)-1
     
    def current_block(self):
        return blocks[current['block']]
    
    def collide(self, position, height):
        pad = 0.25
        p = list(position)
        np = normalize(position)
        for face in FACES: # check all surrounding blocks
            for i in xrange(3): # check each dimension independently
                if not face[i]:
                    continue
                d = (p[i] - np[i]) * face[i]
                if d < pad:
                    continue
                for dy in xrange(height): # check each height
                    op = list(np)
                    op[1] -= dy
                    op[i] += face[i]
                    op = tuple(op)
                    if op not in self.model.world:
                        continue
                    p[i] -= (d - pad) * face[i]
                    if face == (0, -1, 0) or face == (0, 1, 0):
                        self.dy = 0
                    break
        return tuple(p)
        
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if scroll_y < 0:
            return self.change_block(-1)  
        if scroll_y > 0:    
            return self.change_block(1)  
        #x, y, z = self.position
        #dx, dy, dz = self.get_sight_vector()
        #d = scroll_y * 10
        #self.position = (x + dx * d, y + dy * d, z + dz * d)
        
    def on_mouse_press(self, x, y, button, modifiers):
        if self.exclusive:
            vector = self.get_sight_vector()
            block, previous = self.model.hit_test(self.position, vector)
            if button == pyglet.window.mouse.LEFT:
                if block:
                    texture = self.model.world[block]
                    self.model.remove_block(block)
            else:
                if previous:
                    self.model.add_block(previous, self.current_block())
        else:
            self.set_exclusive_mouse(True)
            
    def on_mouse_motion(self, x, y, dx, dy):
        if self.exclusive:
            m = 0.10
            x, y = self.rotation
            x, y = x + dx * m, y + dy * m
            y = max(-90, min(90, y))
            self.rotation = (x, y)
            
            '''
            # I wish to be able to outline the object that is aimd at, if its in range.
            vector = self.get_sight_vector()
            block, cord = self.model.hit_test(self.position, vector)
            if block:
                pass
            '''
            
    def on_key_press(self, symbol, modifiers):
        if symbol == key.W:
            self.strafe[0] -= 1
        elif symbol == key.S:
            self.strafe[0] += 1
        elif symbol == key.A:
            self.strafe[1] -= 1
        elif symbol == key.D:
            self.strafe[1] += 1
        elif symbol == key.SPACE:
            if self.jumping < 2:
                self.jumping += 1
                self.dy = 0.04
        elif symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)
        elif symbol == key.TAB:
            self.flying = not self.flying
            
        elif symbol == key.L:
            SaveWorld(self.model.world)
            
    def on_key_release(self, symbol, modifiers):
        if symbol == key.W:
            self.strafe[0] += 1
        elif symbol == key.S:
            self.strafe[0] -= 1
        elif symbol == key.A:
            self.strafe[1] += 1
        elif symbol == key.D:
            self.strafe[1] -= 1  
            
    def on_resize(self, width, height):
        # label
        self.label.y = height - 10
        # reticle
        if self.reticle:
            self.reticle.delete()
        x, y = self.width / 2, self.height / 2
        n = 10
        self.reticle = pyglet.graphics.vertex_list(4,
            ('v2i', (x - n, y, x + n, y, x, y - n, x, y + n))
        )
        
    def set_2d(self):
        width, height = self.get_size()
        glDisable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    def set_3d(self):
        width, height = self.get_size()
        glEnable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(65.0, width / float(height), 0.1, 60.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        x, y = self.rotation
        glRotatef(x, 0, 1, 0)
        glRotatef(-y, math.cos(math.radians(x)), 0, math.sin(math.radians(x)))
        x, y, z = self.position
        glTranslatef(-x, -y, -z)
    def on_draw(self):
        self.clear()
        self.set_3d()
        glColor3d(1, 1, 1)
        self.model.batch.draw()
        self.set_2d()
        self.draw_label()
        self.draw_reticle()
    
    def draw_label(self):
        x, y, z = self.position
        self.label.text = 'FPS: %02d - POS(%.2f, %.2f, %.2f) %d / %d' % (
            pyglet.clock.get_fps(), x, y, z, 
            len(self.model._shown), len(self.model.world))
        self.label.draw()
        
    def draw_reticle(self):
        glColor3d(0, 0, 0)
        self.reticle.draw(GL_LINES)

def setup_fog():
    glEnable(GL_FOG)
    glFogfv(GL_FOG_COLOR, (c_float * 4)(0.53, 0.81, 0.98, 1))
    glHint(GL_FOG_HINT, GL_DONT_CARE)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_DENSITY, 0.35)
    glFogf(GL_FOG_START, 20.0)
    glFogf(GL_FOG_END, 60.0)

def setup():
    glClearColor(0.50, 0.77, 0.95, 1)
    glEnable(GL_CULL_FACE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    setup_fog()

def main():
    window = Window(width=800, height=600, caption='MicroCraft', resizable=True)
    window.set_exclusive_mouse(True)
    setup()
    pyglet.app.run()

TEXTURE_DATA = textures.TEXTURE_DATA   

if __name__ == '__main__':
    main()
