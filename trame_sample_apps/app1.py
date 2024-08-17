#
from ._base import BaseViewer
from trame.decorators import TrameApp
from vtkmodules.vtkFiltersSources import vtkSphereSource
from vtkmodules.vtkFiltersHybrid import vtkEarthSource
from vtkmodules.vtkRenderingCore import (
    vtkPolyDataMapper,
    vtkActor,
)


@TrameApp()
class Viewer(BaseViewer):
    def generate_actors(self, renderer):
        e = vtkEarthSource()
        e.OutlineOn()
        e.Update()

        e_mapper = vtkPolyDataMapper()
        e_mapper.SetInputConnection(e.GetOutputPort())

        e_actor = vtkActor()
        e_actor.SetMapper(e_mapper)
        e_actor.GetProperty(). \
            SetColor(self._colors.GetColor3d("Black"))

        s = vtkSphereSource()
        s.SetThetaResolution(100)
        s.SetPhiResolution(100)
        s.SetRadius(e.GetRadius())

        s_mapper = vtkPolyDataMapper()
        s_mapper.SetInputConnection(s.GetOutputPort())

        s_actor = vtkActor()
        s_actor.SetMapper(s_mapper)
        s_actor.GetProperty(). \
            SetColor(self._colors.GetColor3d("PeachPuff"))

        return e_actor, s_actor
        # renderer.RemoveAllLights()


def main(**kwargs):
    viewer = Viewer()
    viewer.server.start(**kwargs)


if __name__ == "__main__":
    main()
