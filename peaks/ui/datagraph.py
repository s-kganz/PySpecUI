from kivy_garden.graph import Graph, MeshLinePlot
from pubsub import pub

class MyGraph(Graph):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pub.subscribe(self._add_plot, 'Plot.AddPlot')
        pub.subscribe(self._remove_plot, 'Plot.RemovePlot')
        pub.subscribe(self.clear_all_plots, 'Plot.RemoveAll')

    def clear_all_plots(self):
        '''
        Remove all meshes in the plotting window.
        '''
        meshes = self.plots.copy()
        for mesh in meshes:
            self.remove_plot(mesh)

    def _add_plot(self, trace=None, xmax=0, ymax=0):
        '''
        Add a new trace object to the plot, update graph limits to include
        the entirety of the new data.
        '''
        self._update_envelope(trace)
        super().add_plot(trace)
    
    def _remove_plot(self, trace=None):
        self.remove_plot(trace)
    
    def zoom(self, factor=2):
        '''
        Mutliply the bounds by the factor, causing a zoom.
        '''
        self.xmax = int(self.xmax * factor)
        self.ymax = int(self.ymax * factor)

    def _update_envelope(self, mesh):
        '''
        Updates the plot envelope to contain the incoming mesh, with padding.
        '''
        new_xmin, new_xmax, new_ymin, new_ymax = self._get_mesh_envelope(mesh)
        self.xmin = min(self.xmin, new_xmin)
        self.xmax = max(self.xmax, new_xmax)
        self.ymin = min(self.ymin, new_ymin)
        self.ymax = max(self.ymax, new_ymax)

    def _get_mesh_envelope(self, mesh, padding=0.1):
        '''
        Return the bounding coordinates of a mesh.
        
        Return order: xmin, xmax, ymin, ymax
        '''
        xmin = min(mesh.points, key=lambda x: x[0])[0] 
        xmax = max(mesh.points, key=lambda x: x[0])[0] 
        ymin = min(mesh.points, key=lambda x: x[1])[1]
        ymax = max(mesh.points, key=lambda x: x[1])[1]

        pad_y = abs(ymax * padding)
        pad_x = 0 # abs(xmax * padding)

        return (int(xmin - pad_x), 
               int(xmax + pad_x),
               int(ymin - pad_y),
               int(ymax + pad_y))