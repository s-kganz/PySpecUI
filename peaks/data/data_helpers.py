'''
Mixins for data representation classes.
'''

class Trace():
    '''
    Informal interface for classes that can be plotted.
    '''
    def __init__(self):
        # Set an id if the object did not have one in the derived
        # constructor.
        if not hasattr(self, 'id'):
            self.id = -1
        self.is_plotted = False

    def getx(self):
        '''
        Return the x-axis data for this plottable.
        '''
        raise NotImplementedError("Plottable object must have getx() defined.")

    def gety(self):
        '''
        Return the y-axis data for this plottable.
        '''
        raise NotImplementedError("Plottable object must have gety() defined.")

    def label(self):
        '''
        Label this trace displays when plotted.
        '''
        raise NotImplementedError("Plottable object must have label() defined.")