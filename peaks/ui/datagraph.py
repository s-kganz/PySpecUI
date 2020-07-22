from kivy_garden.graph import Graph, MeshLinePlot
from kivy.graphics import Line, Color
from pubsub import pub

class MyGraph(Graph):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pub.subscribe(self._add_plot, 'Plot.AddPlot')
        pub.subscribe(self._remove_plot, 'Plot.RemovePlot')
        pub.subscribe(self.clear_all_plots, 'Plot.RemoveAll')

        self._touch_down_pos = None

    def clear_all_plots(self):
        '''
        Remove all meshes in the plotting window.
        '''
        meshes = self.plots.copy()
        for mesh in meshes:
            self.remove_plot(mesh)

    def _add_plot(self, trace=None):
        '''
        Add a new trace object to the plot, update graph limits to include
        the entirety of the new data.
        '''
        self._update_envelope(trace)
        super().add_plot(trace.get_mesh())
    
    def _remove_plot(self, trace=None):
        self.remove_plot(trace.get_mesh())
    
    def zoom(self, factor=0.1):
        '''
        Expand the size of the bounding box of the graph by the given factor. A factor of zero
        will not change the bounds at all, a factor of 0.1 expands (i.e. zooms in) by 10%, a factor of -0.1 contracts
        (i.e. zooms out) by 10%, etc.
        '''
        dx = ((self.xmax - self.xmin) * factor) / 2
        dy = ((self.ymax - self.ymin) * factor) / 2

        self.xmax -= dx
        self.xmin += dx
        self.ymax -= dy
        self.ymin += dy

    def _zoom_to(self, xmin, xmax, ymin, ymax):
        '''
        Update the plot envelope to the passed limits (in data space).
        '''
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax

    def _update_envelope(self, trace):
        '''
        Updates the plot envelope to contain the incoming mesh. This differs
        from _zoom_to in that if the trace fits entirely within the existing
        envelope, nothing changes.
        '''
        new_xmin, new_xmax, new_ymin, new_ymax = trace.bounds()
        self.xmin = min(self.xmin, new_xmin)
        self.xmax = max(self.xmax, new_xmax)
        self.ymin = min(self.ymin, new_ymin)
        self.ymax = max(self.ymax, new_ymax)
    
    def _draw_zoom_rectangle(self, p1, p2):
        if self._touch_down_pos is not None:
            with self.canvas.after:
                self.canvas.after.clear()
                Color(1, 0, 0)
                # bottom left, upper left, etc.
                bl = p1
                ul = p1[0], p2[1]
                br = p2[0], p1[1]
                ur = p2
                Line(points=[bl, ul, ur, br, bl])

    def on_touch_down(self, touch):
        if touch.button is not 'right':
            self._touch_down_pos = touch.pos 
        else:
            # TODO show the context menu
            i = 1 
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        if touch.button == 'left':
            self._draw_zoom_rectangle(touch.pos, self._touch_down_pos)
        elif touch.button == 'middle':
            # TODO panning
            i = 1
            #print(touch.dpos)

    
    def on_touch_up(self, touch):
        if touch.button == 'left' and self._touch_down_pos is not None:
            x1, y1 = self.to_data(*self.to_widget(*touch.pos, relative=True))
            x2, y2 = self.to_data(*self.to_widget(*self._touch_down_pos, relative=True))
            
            xmin = min(x1, x2)
            xmax = max(x1, x2)
            ymin = min(y1, y2)
            ymax = max(y1, y2)

            self._zoom_to(xmin, xmax, ymin, ymax)

            self._touch_down_pos = None
            self.canvas.after.clear() # remove the rectangle
        return super().on_touch_up(touch)