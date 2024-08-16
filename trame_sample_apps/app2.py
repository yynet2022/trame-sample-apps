#
import os
import sys
from ._base import BaseViewer
import argparse
from trame.decorators import TrameApp
from vtkmodules.vtkRenderingCore import (  # noqa
    vtkDataSetMapper,
    vtkPolyDataMapper,
    vtkActor,
)
from vtkmodules.vtkIOLegacy import (  # noqa
    vtkUnstructuredGridReader,
    vtkDataSetReader,
)
from vtkmodules.vtkRenderingAnnotation import (  # noqa
    vtkAxesActor,
    vtkCubeAxesActor2D,
    vtkCubeAxesActor,
)


@TrameApp()
class Viewer(BaseViewer):
    def __init__(self, filename, **kwargs):
        self._vtk_filename = filename[0] if len(filename) > 0 else None
        super().__init__(**kwargs)

    @property
    def title(self):
        return self._server.state.trame__title + ': ' + \
            (self._vtk_filename if self._vtk_filename is not None else "")

    def get_actors(self, renderer):
        if self._vtk_filename is None:
            return ()

        # reader = vtkUnstructuredGridReader()
        # vtkDataSetReader は、たぶん
        # vtkPolyDataReader vtkStructuredPointsReader
        # vtkStructuredGridReader vtkRectilinearGridReader
        # vtkUnstructuredGridReader を自動判別してくれる便利クラス
        # ref) IO/Legacy/vtkDataSetReader.cxx
        reader = vtkDataSetReader()
        # reader.DebugOn()  # 使えないらしい
        reader.SetFileName(self._vtk_filename)
        reader.Update()
        if reader.GetErrorCode() != 0:
            raise RuntimeError('Cannot open: ' + self._vtk_filename)

        # mapper = vtkPolyDataMapper()
        # vtkDataSetMapper は vtkDataSetSurfaceFilter + vtkPolyDataMapper
        # のようなもの、かな？
        # ref) Rendering/Core/vtkDataSetMapper.cxx
        mapper = vtkDataSetMapper()
        # mapper.DebugOn()  # こっちも使えないみたい
        mapper.SetInputConnection(reader.GetOutputPort())

        actor = vtkActor()
        actor.SetMapper(mapper)
        prop = actor.GetProperty()
        prop.SetAmbient(0.0)
        prop.SetDiffuse(1.0)
        prop.SetSpecular(0.0)
        prop.SetColor(self._colors.GetColor3d('TestColor'))

        """
        axes = vtkAxesActor()
        b = axes.GetBounds()
        dx = b[1] - b[0]
        dy = b[3] - b[2]
        dz = b[5] - b[4]
        dd = max(dx, dy, dz)
        axes.AddPosition(-dd*0.02, -dd*0.02, -dd*0.02)
        axes.SetTotalLength(dx * 1.2, dy * 1.2, dz * 1.2)

        axes.SetXAxisLabelText("X")
        axes.SetYAxisLabelText("Y")
        axes.SetZAxisLabelText("Z")
        axes.SetShaftTypeToLine()
        axes.SetTipTypeToCone()
        axes.SetConeRadius(0.1)

        # properties of the axes labels can be set as follows
        # this sets the x axis label to red
        axes.GetXAxisCaptionActor2D().GetCaptionTextProperty(). \
            SetColor(self._colors.GetColor3d('Red'))
        """

        print('actor.bounds', actor.GetBounds())
        axes = vtkCubeAxesActor()
        axes.SetUseTextActor3D(1)
        axes.SetBounds(actor.GetBounds())
        axes.SetAxisOrigin(-0.02, -0.02, 0.0)
        # axis.SetUseAxisOrigin(1)

        axisColor = self._colors.GetColor3d('Red')
        # axes.GetTitleTextProperty(0).SetFontSize(54)
        axes.GetTitleTextProperty(0).SetColor(axisColor)
        axes.GetLabelTextProperty(0).SetColor(axisColor)

        axes.GetTitleTextProperty(1).SetColor(axisColor)
        axes.GetLabelTextProperty(1).SetColor(axisColor)

        axes.GetTitleTextProperty(2).SetColor(axisColor)
        axes.GetLabelTextProperty(2).SetColor(axisColor)

        axes.GetXAxesLinesProperty().SetColor(axisColor)
        axes.GetYAxesLinesProperty().SetColor(axisColor)
        axes.GetZAxesLinesProperty().SetColor(axisColor)

        axes.GetXAxesGridlinesProperty().SetColor(axisColor)
        axes.GetYAxesGridlinesProperty().SetColor(axisColor)
        axes.GetZAxesGridlinesProperty().SetColor(axisColor)

        axes.GetXAxesInnerGridlinesProperty().SetColor(axisColor)
        axes.GetYAxesInnerGridlinesProperty().SetColor(axisColor)
        axes.GetZAxesInnerGridlinesProperty().SetColor(axisColor)

        axes.GetXAxesGridpolysProperty().SetColor(axisColor)
        axes.GetYAxesGridpolysProperty().SetColor(axisColor)
        axes.GetZAxesGridpolysProperty().SetColor(axisColor)

        axes.DrawXGridlinesOn()
        axes.DrawYGridlinesOn()
        axes.DrawZGridlinesOn()

        # axes.DrawXInnerGridlinesOn()
        # axes.DrawYInnerGridlinesOn()
        # axes.DrawZInnerGridlinesOn()

        # axes.SetGridLineLocation(VTK_GRID_LINES_FURTHEST)
        # axes.SetGridLineLocation(VTK_GRID_LINES_ALL)
        # axes.SetGridLineLocation(VTK_GRID_LINES_CLOSEST)

        # axes.CenterStickyAxesOn()

        axes.XAxisMinorTickVisibilityOff()
        axes.YAxisMinorTickVisibilityOff()
        axes.ZAxisMinorTickVisibilityOff()

        axes.SetFlyModeToOuterEdges()
        # axis->SetFlyModeToClosestTriad ();
        # axis->SetFlyModeToFurthestTriad ();
        # axis->SetFlyModeToStaticTriad ();
        # axis->SetFlyModeToStaticEdges ();

        # std::cout << "Axes:" << std::endl;
        # axis->PrintSelf (std::cout, vtkIndent(2));

        axes.SetCamera(renderer.GetActiveCamera())

        return actor, axes


def main():
    parser = argparse.ArgumentParser(
        description="VTK Viewer on Web by trame",
        add_help=False,
    )

    parser.add_argument(
        "-h", "--help", action='store_true',
        help="show this help message and trame help message.",
    )
    parser.add_argument(
        "-C", "--client-type",
        default="vue2",
        help="Type of client to use [vue2, vue3]",
    )
    parser.add_argument(
        "--debug", action='store_true',
        help="log debugging messages to stdout",
    )
    parser.add_argument(
        "filename", nargs='*',
        help="VTK file name",
    )

    argv = sys.argv
    argv_trame = [sys.argv[0]]
    if '--' in sys.argv:
        n = sys.argv.index('--')
        argv = sys.argv[:n]
        argv_trame += sys.argv[n+1:]

    opts = parser.parse_args(argv[1:])
    if opts.help:
        print('USAGE:', os.path.basename(argv[0]),
              '[OPTIONS...] [-- TRAME-OPTIONS]')
        print()
        parser.print_help()
        print()
        argv_trame += ['--help']
    elif len(opts.filename) == 0:
        opts.filename.append('a.vtk')

    if opts.debug:
        print('args:', vars(opts))
        argv_trame += ['--debug']
        print('argv_trame', argv_trame)

    try:
        sys.argv = argv_trame
        viewer = Viewer(**vars(opts))
        viewer.server.start()
    except Exception as e:
        print(e, file=sys.stderr)


if __name__ == "__main__":
    main()
