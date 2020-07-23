from kivy_garden.graph import Graph, MeshLinePlot
from kivy.graphics import Line, Color
from kivy.properties import ObjectProperty
from pubsub import pub

class MyGraph(Graph):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pub.subscribe(self._add_plot, 'Plot.AddPlot')
        pub.subscribe(self._remove_plot, 'Plot.RemovePlot')
        pub.subscribe(self.clear_all_plots, 'Plot.RemoveAll')

        self._touch_down_pos = None
        self._traces = []

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
        self._traces.append(trace)
        self._update_current_envelope(trace)
        super().add_plot(trace.get_mesh())
    
    def _remove_plot(self, trace=None):
        self._traces.remove(trace)
        self.remove_plot(trace.get_mesh())
    
    def zoom(self, factor=0.1):
        '''
        Expand the size of the bounding box of the graph by the given factor. A factor of zero
        will not change the bounds at all, a factor of 0.1 expands (i.e. zooms out) by 10%, a factor of -0.1 contracts
        (i.e. zooms in) by 10%, etc.
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
        # Don't allow zooming to a zero-area rectangle
        if xmin == xmax or ymin == ymax: return
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
    
    def fit_to_data(self):
        '''
        Zoom the plotting window to the minimum bounding rectangle necessary
        to show all data.
        '''
        envelope = self._get_minimum_envelope()
        if any(x is None for x in envelope): 
            return
        else:
            self._zoom_to(*envelope)

    def _pan(self, dx, dy):
        '''
        Translate the viewing bounds by dx and dy units (in data space).
        '''
        self.xmin += dx
        self.xmax += dx
        self.ymin += dy
        self.ymax += dy

    def _get_minimum_envelope(self):
        '''
        Determines the smallest bounding rectangle necessary to contain
        all data currently plotted.
        '''
        xmin, xmax, ymin, ymax = None, None, None, None
        for trace in self._traces:
            t_xmin, t_xmax, t_ymin, t_ymax = trace.bounds()
            xmin = t_xmin if xmin is None else min(t_xmin, xmin)
            xmax = t_xmax if xmax is None else max(t_xmax, xmax)
            ymin = t_ymin if ymin is None else min(t_ymin, ymin)
            ymax = t_ymax if ymax is None else max(t_ymax, ymax)
        
        return xmin, xmax, ymin, ymax

    def _update_current_envelope(self, trace):
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
        if not self.collide_point(*touch.pos): return
        if touch.is_mouse_scrolling:
            if touch.button == 'scrolldown':
                self.zoom(factor=0.5)
            else:
                self.zoom(factor=-0.5)
        elif touch.button is not 'right':
            self._touch_down_pos = touch.pos 
        else:
            self.context.show() 
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        if touch.button == 'left':
            # Update the zoom rectangle
            self._draw_zoom_rectangle(touch.pos, self._touch_down_pos)
        elif touch.button == 'middle':
            # Pan the graph with the cursor
            oldx, oldy = self.to_data(*self.to_widget(*self._touch_down_pos, relative=True))
            newx, newy = self.to_data(*self.to_widget(*touch.pos, relative=True))
            self._pan(oldx - newx, oldy - newy) # negate change in coords so pointer travels with data
            self._touch_down_pos = touch.pos
    
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