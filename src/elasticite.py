#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import
import os
import numpy as np
import time
import vapory

DEBUG = False

#import matplotlib
#matplotlib.use("Agg") # agg-backend, so we can create figures without x-server (no PDF, just PNG etc.)
#import matplotlib.pyplot as plt
#
# https://zeromq.github.io/pyzmq/serialization.html
def send_array(socket, A, flags=0, copy=True, track=False):
    """send a numpy array with metadata"""
    md = dict(
        dtype = str(A.dtype),
        shape = A.shape,
    )
    socket.send_json(md, flags|zmq.SNDMORE)
    return socket.send(A, flags, copy=copy, track=track)

def recv_array(socket, flags=0, copy=True, track=False):
    """recv a numpy array"""
    md = socket.recv_json(flags=flags)
    msg = socket.recv(flags=flags, copy=copy, track=track)
    # buf = buffer(msg)
    A = np.frombuffer(msg, dtype=md['dtype'])
    return A.reshape(md['shape'])

import inspect
def get_default_args(func):
    """
    returns a dictionary of arg_name:default_values for the input function
    """
    args, varargs, keywords, defaults = inspect.getargspec(func)
    return dict(zip(args[-len(defaults):], defaults))

# from  multiprocessing import Process

class EdgeGrid():
    def __init__(self,
                 N_lame = 8*72,
                 N_lame_X = None,
                 figsize = 13,
                 line_width = 4.,
                 grid_type = 'hex',
		 structure = True,
                 verb = False,
                 mode = 'both',
                 ):
        self.t0 = self.time(True)
        self.t = self.time()
        self.dt = self.t - self.t0
        self.verb = verb
        self.display = (mode=='display') or (mode=='both')
        self.stream =  (mode=='stream') or (mode=='display')
        #if mode=='display': self.stream = True
        self.serial =  (mode=='serial') # converting a stream to the serial port to control the arduino

        self.port = "5556"
        # moteur:
        self.serial_port, self.baud_rate = '/dev/ttyACM0', 230400
        # 1.8 deg par pas (=200 pas par tour) x 32 divisions de pas
        # demultiplication : pignon1= 14 dents, pignon2 = 40 dents
        self.n_pas = 200. * 32. * 40 / 14

        # taille installation
        self.total_width = 5 # en mètres        
        self.lame_height = 3 # en mètres
        self.background_depth = 100 # taille du 104 en profondeur
        self.f = .1

        self.figsize = figsize
        self.line_width = line_width
        self.grid_type = grid_type
        self.grid(N_lame=N_lame, N_lame_X=N_lame_X)
        self.lames[2, :] = np.pi*np.random.rand(self.N_lame)
        self.structure = structure
        #if self.structure:
        #    self.N_lame += 6


    def time(self, init=False):
        if init: return time.time()
        else: return time.time() - self.t0
        
    def grid(self, N_lame, N_lame_X):

        self.N_lame = N_lame
        #if N_lame_X is None:

        if self.grid_type=='hex':
            self.N_lame_X = np.int(np.sqrt(self.N_lame))#*np.sqrt(3) / 2)
            self.lames = np.zeros((4, self.N_lame))
            self.lames[0, :] = np.mod(np.arange(self.N_lame), self.N_lame_X)
            self.lames[0, :] += np.mod(np.floor(np.arange(self.N_lame)/self.N_lame_X), 2)/2
            self.lames[1, :] = np.floor(np.arange(self.N_lame)/self.N_lame_X)
            self.lames[1, :] *= np.sqrt(3) / 2
            self.lames[0, :] /= self.N_lame_X
            self.lames[1, :] /= self.N_lame_X
            self.lames[0, :] += .5/self.N_lame_X - .5
            self.lames[1, :] += 1.5/self.N_lame_X # TODO : prove analytically
            self.lames[0, :] *= self.total_width
            self.lames[1, :] *= self.total_width
            self.lame_length = .99/self.N_lame_X*self.total_width*np.ones(self.N_lame)
            self.lame_width = .03/self.N_lame_X*self.total_width*np.ones(self.N_lame)
        elif self.grid_type=='line':
            self.N_lame_X = self.N_lame
            self.lames = np.zeros((4, self.N_lame))
            self.lames[0, :] = np.linspace(-self.total_width/2, self.total_width/2, self.N_lame, endpoint=True)
            self.lames[1, :] = self.total_width/2
            self.lame_length = .12*np.ones(self.N_lame) # en mètres
            self.lame_width = .042*np.ones(self.N_lame) # en mètres

        self.lames_minmax = np.array([self.lames[0, :].min(), self.lames[0, :].max(), self.lames[1, :].min(), self.lames[1, :].max()])
        #print(self.lames_minmax)

        #print(self.lame_length)
        #self.lines = self.set_lines()

        #if self.structure:
        #    self.N_lame += 6

    def structure(self, position=[0., 3.5], longueur=3, angles=[15., 65., 102.]):
        
        
        return "toto"

    def theta_E(self, im, X_, Y_, w):
        try:
            assert(self.slip.N_X==im.shape[1])
        except:
            from NeuroTools.parameters import ParameterSet
            from SLIP import Image
            from LogGabor import LogGabor
            self.slip = Image(ParameterSet({'N_X':im.shape[1], 'N_Y':im.shape[0]}))
            self.lg = LogGabor(self.slip)
        im_ = im.sum(axis=-1)
        im_ = im_ * np.exp(-.5*((.5 + .5*self.slip.x-Y_)**2+(.5 + .5*self.slip.y-X_)**2)/w**2)
        E = np.zeros((self.N_theta,))
        for i_theta, theta in enumerate(self.thetas):
            params= {'sf_0':self.sf_0, 'B_sf':self.B_sf, 'theta':theta, 'B_theta': np.pi/self.N_theta}
            FT_lg = self.lg.loggabor(0, 0, **params)
            E[i_theta] = np.sum(np.absolute(self.slip.FTfilter(np.rot90(im_, -1), FT_lg, full=True))**2)
        return E

    def theta_max(self, im, X_, Y_, w):
        E = self.theta_E(im, X_, Y_, w)
        return self.thetas[np.argmax(E)] - np.pi/2


    def theta_sobel(self, im, N_blur):
        im_ = im.copy()
        sobel = np.array([[1,   2,  1,],
                          [0,   0,  0,],
                          [-1, -2, -1,]])
        if im_.ndim==3: im_ = im_.sum(axis=-1)
        from scipy.signal import convolve2d
        im_X = convolve2d(im_, sobel, 'same')
        im_Y = convolve2d(im_, sobel.T, 'same')

        N_X, N_Y = im_.shape
        x, y = np.mgrid[0:1:1j*N_X, 0:1:1j*N_Y]
        mask = np.exp(-.5*((x-.5)**2+(y-.5)**2)/w**2)
        im_X = convolve2d(im_X, mask, 'same')
        im_Y = convolve2d(im_Y, mask, 'same')
        blur = np.array([[1, 2, 1],
                         [2, 8, 2],
                         [1, 2, 1]])
        for i in range(N_blur):
            im_X = convolve2d(im_X, blur, 'same')
            im_Y = convolve2d(im_Y, blur, 'same')

        angle = np.arctan2(im_Y, im_X)

        bord = .1
        angles = np.empty(self.N_lame)
        N_X, N_Y = im_.shape
        for i in range(self.N_lame):
            angles[i] = angle[int((bord+self.lames[0, i]*(1-2*bord))*N_X),
                              int((bord+self.lames[1, i]*(1-2*bord))*N_Y)]
        return angles - np.pi/2

    def pos_rel(self, do_torus=False):
        def torus(x, w=1.):
            """
            center x in the range [-w/2., w/2.]

            To see what this does, try out:
            >> x = np.linspace(-4,4,100)
            >> pylab.plot(x, torus(x, 2.))

            """
            return np.mod(x + w/2., w) - w/2.
        dx = self.lames[0, :, np.newaxis]-self.lames[0, np.newaxis, :]
        dy = self.lames[1, :, np.newaxis]-self.lames[1, np.newaxis, :]
        if do_torus:
            return torus(dx), torus(dy)
        else:
            return dx, dy

    def distance(self, do_torus=False):
        dx, dy = self.pos_rel(do_torus=do_torus) 
        return np.sqrt(dx **2 + dy **2)

    def angle_relatif(self):
        return self.lames[2, :, np.newaxis]-self.lames[2, np.newaxis, :]

    def angle_cocir(self, do_torus=False):
        dx, dy = self.pos_rel(do_torus=do_torus)
        theta = self.angle_relatif()
        return np.arctan2(dy, dx) - np.pi/2 - theta

    def champ(self):
        force = np.zeros_like(self.lames[2, :])
        noise = lambda t: 0.2 * np.exp((np.cos(2*np.pi*(t-0.) / 6.)-1.)/ 1.5**2)
        damp = lambda t: 0.01 #* np.exp(np.cos(t / 6.) / 3.**2)
        colin_t = lambda t: -.1*np.exp((np.cos(2*np.pi*(t-2.) / 6.)-1.)/ .3**2)
        cocir_t = lambda t: -4.*np.exp((np.cos(2*np.pi*(t-4.) / 6.)-1.)/ .5**2)
        cocir_d = lambda d: np.exp(-d/.05)
        colin_d = lambda d: np.exp(-d/.2)

        force += colin_t(self.t) * np.sum(np.sin(2*(self.angle_relatif()))*colin_d(self.distance()), axis=1)
        force += cocir_t(self.t) * np.sum(np.sin(2*(self.angle_cocir()))*cocir_d(self.distance()), axis=1)
        force += noise(self.t)*np.pi*np.random.randn(self.N_lame)
        force -= damp(self.t) * self.lames[3, :]/self.dt
        return 42.*force

    def update(self):
        self.lames[2, :] += self.lames[3, :]*self.dt/2
        self.lames[3, :] += self.champ() * self.dt
        self.lames[2, :] += self.lames[3, :]*self.dt/2
        
    def render(self, fps=10, W=1000, H=618, location=[0, 1.75, -2], head_size=.4, light_intensity=1.2, reflection=1., 
               look_at=[0, 1.5, 0], antialiasing=0.001, duration=5, fname='/tmp/temp.webm'):

        def scene(t):
            """ 
            Returns the scene at time 't' (in seconds) 
            """

            head_location = np.array(location) - np.array([0, 0, head_size])
            import vapory
            light = vapory.LightSource([15, 15, 1], 'color', [light_intensity]*3)
            background = vapory.Box([0, 0, 0], [1, 1, 1], 
                     vapory.Texture(vapory.Pigment(vapory.ImageMap('png', '"../files/VISUEL_104.png"', 'once')),
                             vapory.Finish('ambient', 1.2) ),
                     'scale', [self.background_depth, self.background_depth, 0],
                     'translate', [-self.background_depth/2, -.45*self.background_depth, -self.background_depth/2])
            me = vapory.Sphere( head_location, head_size, vapory.Texture( vapory.Pigment( 'color', [1, 0, 1] )))
            self.t = t
            self.update()
            objects = [background, me, light]

            for i_lame in range(self.N_lame):
                print(i_lame, self.lame_length[i_lame], self.lame_width[i_lame])
                objects.append(vapory.Box([-self.lame_length[i_lame]/2, 0, -self.lame_width[i_lame]/2], 
                                          [self.lame_length[i_lame]/2, self.lame_height,  self.lame_width[i_lame]/2], 
                                           vapory.Pigment('color', [1, 1, 1]),
                                           vapory.Finish('phong', 0.8, 'reflection', reflection),
                                           'rotate', (0, -self.lames[2, i_lame]*180/np.pi, 0), #HACK?
                                           'translate', (self.lames[0, i_lame], 0, self.lames[1, i_lame])
                                          )
                              )

            objects.append(light)
            return vapory.Scene( vapory.Camera("location", location, "look_at", look_at),
                           objects = objects,
                           included=["glass.inc"] )
        import moviepy.editor as mpy
        if not os.path.isfile(fname):
            self.dt = 1./fps
            def make_frame(t):
                return scene(t).render(width=W, height=H, antialiasing=antialiasing)

            clip = mpy.VideoClip(make_frame, duration=duration)
            clip.write_videofile(fname, fps=fps)
        return mpy.ipython_display(fname, fps=fps, loop=1, autoplay=1)

    #def show_edges(self, fig=None, a=None):
        #self.N_theta = 12
        #self.thetas = np.linspace(0, np.pi, self.N_theta)
        #self.sf_0 = .3
        #self.B_sf = .3
#
        #self.vext = '.webm'
        #self.figpath = '../files/figures/elasticite/'
        #self.fps = 25
        #"""
        #Shows the quiver plot of a set of edges, optionally associated to an image.
#
        #"""
        #import pylab
        #import matplotlib.cm as cm
        #if fig==None:
            #fig = pylab.figure(figsize=(self.figsize, self.figsize))
        #if a==None:
            #border = 0.0
            #a = fig.add_axes((border, border, 1.-2*border, 1.-2*border), axisbg='w')
        #else:
            #self.update_lines()
        #marge = self.lame_length*3.
        #a.axis(self.lames_minmax + np.array([-marge, +marge, -marge, +marge]))
        #a.add_collection(self.lines)
        #a.axis(c='b', lw=0)
        #pylab.setp(a, xticks=[])
        #pylab.setp(a, yticks=[])
        #pylab.draw()
        #return fig, a

    #def set_lines(self):
        #from matplotlib.collections import LineCollection
        #import matplotlib.patches as patches
        # draw the segments
        #segments, colors, linewidths = list(), list(), list()
#
        #X, Y, Theta = self.lames[0, :], self.lames[1, :].real, self.lames[2, :]
        #for x, y, theta in zip(X, Y, Theta):
            #u_, v_ = np.cos(theta)*self.lame_length, np.sin(theta)*self.lame_length
            #segments.append([(x - u_, y - v_), (x + u_, y + v_)])
            #colors.append((0, 0, 0, 1))# black
            #linewidths.append(self.line_width)
        #return LineCollection(segments, linewidths=linewidths, colors=colors, linestyles='solid')
#
    #def update_lines(self):
        #from matplotlib.collections import LineCollection
        #import matplotlib.patches as patches
        #X, Y, Theta = self.lames[0, :], self.lames[1, :], self.lames[2, :]
        #segments = list()
#
        #for i, (x, y, theta) in enumerate(zip(X, Y, Theta)):
            #u_, v_ = np.cos(theta)*self.lame_length, np.sin(theta)*self.lame_length
            #segments.append([(x - u_, y - v_), (x + u_, y + v_)])
        #self.lines.set_segments(segments)
#
#
    #def fname(self, name):
        #return os.path.join(self.figpath, name + self.vext)
#
    #def make_anim(self, name, make_lames, duration=3., redo=False):
        #if redo or not os.path.isfile(self.fname(name)):
#
            #import matplotlib.pyplot as plt
            #from moviepy.video.io.bindings import mplfig_to_npimage
            #import moviepy.editor as mpy
#
            #fig_mpl, ax = plt.subplots(1, figsize=(self.figsize, self.figsize), facecolor='white')
#
            #def make_frame_mpl(t):
                # on ne peut changer que l'orientation des lames:
                #self.t = t
                #self.lames[2, :] = make_lames(self)
                #self.update_lines()
                #fig_mpl, ax = self.show_edges()#fig_mpl, ax)
                #self.t_old = t
                #return mplfig_to_npimage(fig_mpl) # RGB image of the figure
#
            #animation = mpy.VideoClip(make_frame_mpl, duration=duration)
            #animation.write_videofile(self.fname(name), fps=self.fps)
#
    #def ipython_display(self, name, loop=True, autoplay=True, controls=True):
        #"""
        #showing the grid in the notebook by pointing at the file stored in the proper folder
#
        #"""
        #import os
        #from IPython.core.display import display, Image, HTML
        #opts = ' '
        #if loop: opts += 'loop="1" '
        #if autoplay: opts += 'autoplay="1" '
        #if controls: opts += 'controls '
        #s = """
            #<center><table border=none width=100% height=100%>
            #<tr> <td width=100%><center><video {0} src="{2}" type="video/{1}"  width=100%>
            #</td></tr></table></center>""".format(opts, self.vext[1:], self.fname(name))
        #return display(HTML(s))
#
try:
    import pyglet
    from pyglet.gl.glu import gluLookAt
    import pyglet.gl as gl
    smoothConfig = gl.Config(sample_buffers=1, samples=4,
                             depth_size=16, double_buffer=True)
except:
    print('Could not load pyglet')

class Window(pyglet.window.Window):
    """
    Viewing particles using pyglet.app

        Interaction keyboard:
        - TAB pour passer/sortir du fulscreen
        - espace : passage en first-person perspective

        Les interactions visuo - sonores sont simulées ici par des switches lançant des phases:
        - F : faster
        - S : slower

    """
    def __init__(self, e, *args, **kwargs):
        #super(Window, self).__init__(*args, **kwargs)
        super(Window, self).__init__(config=smoothConfig, *args, **kwargs)
        self.e = e

    #@self.event
    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.TAB:
            if self.fullscreen:
                self.set_fullscreen(False)
                self.set_location(screen.width/3, screen.height/3)
            else:
                self.set_fullscreen(True)
        elif symbol == pyglet.window.key.ESCAPE:
            pyglet.app.exit()
        elif symbol == pyglet.window.key.S:
            self.e.f /= 1.05
        elif symbol == pyglet.window.key.F:
            self.e.f *= 1.05

#
    #@self.win.event
    def on_resize(self, width, height):
        print('The window was resized to %dx%d' % (width, height))
#
    #@self.win.event
    def on_draw(self):
        if self.e.stream:
            if self.e.verb: print("Sending request")
            self.e.socket.send (b"Hello")
            #message = self.e.socket.recv()
            #print "Received reply ", message
            #return

            X, Y, Theta = self.e.lames[0, :], self.e.lames[1, :], recv_array(self.e.socket)
            if self.e.verb: print("Received reply ", Theta.shape)
        else:
            self.e.dt = self.e.time() - self.e.t
            self.e.update()
            self.e.t = self.e.time()
            X, Y, Theta = self.e.lames[0, :], self.e.lames[1, :], self.e.lames[2, :]

        self.W = float(self.width)/self.height
        self.clear()
        gl.glMatrixMode(gl.GL_PROJECTION);
        gl.glLoadIdentity()
#                     gluOrtho2D sets up a two-dimensional orthographic viewing region.  
#          Parameters left, right
#                             Specify the coordinates for the left and right vertical clipping planes.
#                         bottom, top
#                             Specify the coordinates for the bottom and top horizontal clipping planes.
#                         Description
#         gl.gluOrtho2D(-(self.W-1)/2*self.e.total_width, (self.W+1)/2*self.e.total_width, -self.e.total_width/2, self.e.total_width/2, 0, 0, 1);
        gl.gluOrtho2D(-self.W/2*self.e.total_width, self.W/2*self.e.total_width, 0, self.e.total_width, 0, 0, 1);
        gl.glMatrixMode(gl.GL_MODELVIEW);
        gl.glLoadIdentity();

        #gl.glLineWidth () #p['line_width'])
        gl.glEnable (gl.GL_BLEND)
        #gl.glHint(gl.GL_LINE_SMOOTH_HINT, gl.GL_NICEST)
        gl.glColor3f(0., 0., 0.)
        dX, dY = np.cos(Theta)/2., np.sin(Theta)/2.
        # coords = np.vstack((X-dX*self.e.lame_length, Y-dY*self.e.lame_length, X+dX*self.e.lame_length, Y+dY*self.e.lame_length))
        coords = np.vstack((
                            X-dX*self.e.lame_length+dY*self.e.lame_width, Y-dY*self.e.lame_length-dX*self.e.lame_width,
                            X+dX*self.e.lame_length+dY*self.e.lame_width, Y+dY*self.e.lame_length-dX*self.e.lame_width,
                            X-dX*self.e.lame_length-dY*self.e.lame_width, Y-dY*self.e.lame_length+dX*self.e.lame_width,
                            X+dX*self.e.lame_length-dY*self.e.lame_width, Y+dY*self.e.lame_length+dX*self.e.lame_width,
                            ))
        #pyglet.graphics.draw(2*self.e.N_lame, gl.GL_LINES, ('v2f', coords.T.ravel().tolist()))
        indices = np.array([0, 1, 2, 1, 2, 3])[:, np.newaxis] + 4*np.arange(self.e.N_lame)
        pyglet.graphics.draw_indexed(4*self.e.N_lame, pyglet.gl.GL_TRIANGLES,
                                     indices.T.ravel().tolist(),
                                     ('v2f', coords.T.ravel().tolist()))
        #pyglet.graphics.draw(4*self.e.N_lame, gl.GL_QUADS, ('v2f', coords.T.ravel().tolist()))
        # carré
        if DEBUG:
            coords = np.array([[0., self.e.total_width, self.e.total_width, 0.], [0., 0., self.e.total_width, self.e.total_width]])
            pyglet.graphics.draw(4, gl.GL_LINE_LOOP, ('v2f', coords.T.ravel().tolist()))
        # centres des lames
        if DEBUG:
            pyglet.graphics.draw(self.e.N_lame, gl.GL_POINTS, ('v2f', self.e.lames[:2,:].T.ravel().tolist()))
#
def server(e):
    import zmq
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:%s" % e.port)
    if e.verb: print("Running server on port: ", e.port)
    # serves only 5 request and dies
    while True:
        # Wait for next request from client
        message = socket.recv()
        if e.verb: print("Received request %s" % message)
        e.dt = e.time() - e.t
        e.update()
        e.t = e.time()
        send_array(socket, e.lames[2, :])

def serial(e):
    import serial
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVwXYZabcdefghijklmnopqrstuvwxyz'
    def convert(increment):
        #msg  = ''
        #for i in len(increment):
        #    msg += alphabet(i) + str(increment[i])  + ';' 
        msg = sum([alphabet(i) + str(increment[i])  + ';' for i in len(increment)]) 
        return msg  
    
    with serial.Serial(e.serial_port, e.baud_rate) as ser:
        if e.verb: print("Running serial on port: ", e.serial_port)
        nbpas_old = np.zeros_like(e.lames[2, :], dtype=np.int)
        while True:
            e.dt = e.time() - e.t
            e.update()
            e.t = e.time()
            nbpas = [int(theta*e.n_pas) for theta in e.lames[2, :]]
            dnbpas =  nbpas - nbpas_old
            nbpas_old = nbpas_old + dnbpas
            if e.verb: print(e.t, convert(dnbpas))
            ser.write(convert(dnbpas))

def client(e):
    if e.stream:
        import zmq
        context = zmq.Context()
        if e.verb: print("Connecting to server with port %s" % e.port)
        e.socket = context.socket(zmq.REQ)
        e.socket.connect ("tcp://localhost:%s" % e.port)

    platform = pyglet.window.get_platform()
    print("platform" , platform)
    display = platform.get_default_display()
    print("display" , display)
    screens = display.get_screens()
    print("screens" , screens)
    for i, screen in enumerate(screens):
        print('Screen %d: %dx%d at (%d,%d)' % (i, screen.width, screen.height, screen.x, screen.y))
    N_screen = len(screens) # number of screens
    N_screen = 1# len(screens) # number of screens
    assert N_screen == 1 # we should be running on one screen only
    def callback(dt):
        if e.verb: print('%f seconds since last callback' % dt , '%f  fps' % pyglet.clock.get_fps())
        pass
    window = Window(e, width=screen.width*2/3, height=screen.height*2/3)
    window.set_location(screen.width/3, screen.height/3)
    pyglet.gl.glClearColor(1., 1., 1., 1.)
    pyglet.clock.schedule(callback)
    pyglet.app.run()

def main(e):
#     print(e.display, e.stream)
    # Now we can run the server
    if e.display:
        # Now we can connect a client to the server
        #Process(target=client, args=(e,)).start()
        client(e)

    elif e.stream:
        #Process(target=server, args=(e,)).start()
        server(e)

    elif e.serial:
        #Process(target=server, args=(e,)).start()
        serial(e)

if __name__ == '__main__':
    e = EdgeGrid()
    main(e)

