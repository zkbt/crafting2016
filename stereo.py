#!/usr/bin/env python

import os, sys, warnings, optparse, numpy as np, matplotlib.pyplot as plt
warnings.filterwarnings("ignore")
from PIL import Image


class iplot():
    def __init__(self, nRows, nCols, verbose=True, **kwargs):
        # input number of rows and number of columns
        # keep track of messages
        self.verbose = verbose
        self.prefix = '   [i] '
        if self.verbose:
            print self.prefix + 'creating an interactive figure'
            self.indent()

        # create a gridspec object
        self.gs = plt.matplotlib.gridspec.GridSpec(nRows,nCols,**kwargs)
        self.figure = plt.gcf()
        self.figure.set_facecolor('white')
        # create an empty dictionary to store axes
        self.axes = {}

        plt.show(block=False)

    def indent(self):
        self.prefix = ' ' + self.prefix

    def unindent(self):
        self.prefix = self.prefix[1:]

    def subplot(self, row=0, col=0,rowspan=1,colspan=1,name=None, **kwargs):
        # create the axis object, using the gridspec language
        #    for example,

        ax = plt.subplot(self.gs[row:row + rowspan, col:col + colspan], **kwargs)
        if name == None:
            name = 'ax{0}'.format(len(self.axes))
        self.axes[name] = ax
        if self.verbose:
            print self.prefix + 'added axes at rows {0}-{1} and columns {2}-{3}, named {4}'.format(row,row + rowspan, col,col + colspan,name)
        return ax

    def connect(self):
        # connect all the event-handling functions
        #self.figure.canvas.mpl_connect('axes_enter_event', self.onEnterAxes)
        #self.figure.canvas.mpl_connect('axes_leave_event', self.onLeaveAxes)
        self.cids = []
        self.cids.append(self.figure.canvas.mpl_connect('button_release_event', self.onClick))

    def onEnterAxes(self, event):
        print 'enter_axes', event.inaxes
        event.inaxes.patch.set_facecolor('yellow')
        event.canvas.draw()

    def onLeaveAxes(self, event):
        print 'leave_axes', event.inaxes
        event.inaxes.patch.set_facecolor('white')
        event.canvas.draw()

    def onClick(self, event):
        if event.xdata is None:
            print self.prefix + " that wasn't a very nice click. Could you please try again?"
            return
        if self.verbose:
            print self.prefix + ' clicked at {0}, {1}'.format(event.xdata, event.ydata)
        self.lastMouseClick = event


        self.mouseClicks.append(event)
        self.remainingClicks -= 1
        if self.remainingClicks <= 0:
            self.stop()

    def getMouseClicks(self, n=2):
        # say what's happening
        if self.verbose:
            print self.prefix + "waiting for {0} mouse clicks.".format(n)
            self.indent()

        # set the countdown for the number of clicks
        self.remainingClicks = n
        self.mouseClicks = []

        # start the event handling loop
        self.start()

        self.unindent()
        # return a list of mouse clicks, which the loop should have generated
        return self.mouseClicks

    def start(self):
        self.connect()
        plt.draw()
        self.figure.canvas.start_event_loop(0)

    def stop(self):
        self.figure.canvas.stop_event_loop()
        for cid in self.cids:
            self.figure.canvas.mpl_disconnect(cid)


class Stereo(object):
    '''A parent class for stereographic images.'''
    def __init__(self, *args):
        '''Initialize a new image'''

        # is the first argument a pre-loaded stereo image?
        try:
            # if so, use it!
            self.left, self.right = args[0].left, args[0].right
        except AttributeError:
            # if not, load the images from scratch!
            self.load(*args)

    def load(self, leftFilename, rightFilename):
        '''Load in images for the left and right eyes, and store them.'''

        print ' Reading input images.'
        self.filenames = dict(left=leftFilename, right=rightFilename)

        # loop over the eyes, loading the image for each
        for k in ['left', 'right']:
            print "  loading {eye} eye's image from {filename}".format(eye=k, filename=self.filenames[k])
            # store images in self.left and self.right
            self.__dict__[k] = Image.open(self.filenames[k])
            print "   success!"

    def adjust(self):
        '''Let user click to identify a feature to line up in both images.'''

        self.iplot = iplot(1,2,verbose=False,hspace=0,wspace=0)
        self.iplot.subplot(0,0,name='left')
        self.iplot.subplot(0,1,name='right')
        for k in ['left', 'right']:
            ax = self.iplot.axes[k]
            ax.imshow(self.__dict__[k], interpolation='nearest')
            ylim = ax.get_ylim()
            ax.set_ylim(max(ylim), min(ylim))
            ax.set_title(k.capitalize())
            plt.setp(ax.get_yticklabels(), visible=False)
            plt.setp(ax.get_xticklabels(), visible=False)
        print " Please click the same feature in boths images."
        print "  (the images will be aligned to match up on this feature, to draw the viewer's focus)"
        self.referencepoints = {}
        while(len(self.referencepoints.keys())<2):
            click = self.iplot.getMouseClicks(1)[0]
            for k in self.iplot.axes.keys():
                if self.iplot.axes[k] == click.inaxes:
                    whicheye = k
                    self.referencepoints[k] = np.round(np.array([click.xdata, click.ydata])).astype(np.int)
            print "  You clicked the {0} image at {1}".format(whicheye, self.referencepoints[whicheye])
            #self.iplot.axes[whicheye].scatter(*self.referencepoints[whicheye], s=50)
        nudgex, nudgey = self.referencepoints['right']-self.referencepoints['left']

        print  " Applying a nudge of {0} pixels between the two images.".format((nudgex,nudgey))
        left, right = np.array(self.left), np.array(self.right)
        if nudgex > 0:
            left = left[:,:-nudgex]
            right = right[:,nudgex:]
        else:
            left = left[:,-nudgex:]
            right = right[:,:nudgex]
        if nudgey > 0:
            left = left[:-nudgey, :]
            right = right[nudgey:, :]
        else:
            left = left[-nudgey:, :]
            right = right[:nudgey, :]
        self.left, self.right = Image.fromarray(left), Image.fromarray(right)

    def filename(self, i):
        '''Construct a filename, given a label number.'''
        return 'stereoscopic_{label}_{i:03.0f}.jpg'.format(label=self.label, i=i)

    def save(self):
        '''Save a stereoscopic image, being careful not to write over others.'''
        i=0
        while(os.path.exists(self.filename(i))):
            i += 1
        self.combined.save(self.filename(i))
        print "   saved to {0}".format(self.filename(i))

class SideBySide(Stereo):
    '''A stereoscopic image object, where images are shown side-by-side.'''

    # set the label
    label = 'sidebyside'

    def display(self):
        '''Output the stereo image.'''

        print " Saving stero image in side-by-side format."

        # convert images to arrays, but keep them as colors (width x height x 3)
        left = np.array(self.left)
        right = np.array(self.right)

        # construct a comined image by stacking the images side by side
        self.combined = Image.fromarray(np.hstack([left,right]))

        # output the image
        self.save()


class Anaglyph(Stereo):
    '''A stereoscopic image object, making images for blue-red glasses.'''

    # set the label
    label = 'bluered'

    def display(self):
        '''Output the stereo image.'''

        print " Saving stero image in red-blue (anaglyph) format."

        # first convert images to black and white (width x height)
        left = np.array(self.left.convert('L'))
        right = np.array(self.right.convert('L'))

        # construct a combined image by populating the RGB channels
        merged = np.zeros_like(np.array(self.left))
        merged[:,:,0] += left
        merged[:,:,1] += right
        merged[:,:,2] += right
        self.combined = Image.fromarray(merged)
        self.combined.show()
        # output the image
        self.save()


def nextfilename(guess):
    '''Make a new filename, incrementing the number if need be.'''
    g = glob.glob(guess)


#s = Stereo('couchtest/left.jpg','couchtest/right.jpg')
if __name__ == '__main__':

    print ""

    # parse the input options
    parser = optparse.OptionParser(usage = """
    ./stereo.py [options] left_image right_image

Options:
    -a, --auto = skip the alignment step""")

    # figure out which options have been set, and the image filenames
    parser.add_option('-a', '--auto',
        action = 'store_const', const = True, dest = 'automatic', default=False,
        help = 'skip the adjustment step (this assumes your images are perfectly aligned)')
    options, args = parser.parse_args()

    # complain if the wrong number of filenames is included
    if len(args) != 2:
        parser.error("""Hmmm...there are {0} arguments to ./stereo.py.
                        Please run with two image filenames.
                        (e.g. "./stereo.py leftimage.jpg rightimage.jpg")
                        """.format(len(args)))

    # create the stereo image
    print "Creating a stereo image from your two input images!"
    s = Stereo(*args)


    # unless the "--auto" option is set,
    if options.automatic == False:
        s.adjust()

    # create a side-by-side image
    sbs = SideBySide(s)
    sbs.display()

    # create a blue-red image
    a = Anaglyph(s)
    a.display()

    print "Done! Put on your glasses and check out your stereogram!"
