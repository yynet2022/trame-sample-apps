#
import os
import sys
import argparse
from pathlib import Path

from ._base import BaseViewer
from trame.decorators import TrameApp, change
from trame.widgets import vuetify
from vtkmodules.vtkCommonCore import (
    vtkLookupTable,
    vtkUnsignedCharArray,
)
from vtkmodules.vtkRenderingCore import (  # noqa
    vtkDataSetMapper,
    vtkPolyDataMapper,
    vtkActor,
)
from vtkmodules.vtkIOLegacy import (  # noqa
    vtkUnstructuredGridReader,
    vtkDataSetReader,
)
from vtkmodules.vtkIOXML import (  # noqa
    vtkXMLGenericDataObjectReader,
    vtkXMLUnstructuredGridReader,
    vtkXMLPolyDataReader,
    vtkXMLStructuredGridReader,
    vtkXMLRectilinearGridReader,
    vtkXMLImageDataReader,
    vtkXMLMultiBlockDataReader,
    vtkXMLHyperTreeGridReader,
)
from vtkmodules.vtkIOPLY import vtkPLYReader
from vtkmodules.vtkIOGeometry import vtkOBJReader, vtkSTLReader, vtkBYUReader
from vtkmodules.vtkCommonDataModel import (  # noqa
    vtkDataSet,
    vtkCompositeDataSet,
    vtkDataObjectTreeIterator,
    vtkDataObject,
)
from vtkmodules.vtkRenderingAnnotation import (  # noqa
    vtkAxesActor,
    vtkCubeAxesActor2D,
    vtkCubeAxesActor,
    vtkScalarBarActor,
)

assert sys.version_info[:2] >= (3, 10), "Python 3.10 required"  # noqa

READERCLASS = {
    ".vtu": vtkXMLUnstructuredGridReader,
    ".vtp": vtkXMLPolyDataReader,
    ".vts": vtkXMLStructuredGridReader,
    ".vtr": vtkXMLRectilinearGridReader,
    ".vti": vtkXMLImageDataReader,
    ".vtm": vtkXMLMultiBlockDataReader,
    ".vto": vtkXMLHyperTreeGridReader,
    ".vtk": vtkDataSetReader,
    ".ply":  vtkPLYReader,
    ".obj":  vtkOBJReader,
    ".stl":  vtkSTLReader,
    ".g":    vtkBYUReader,
}


@TrameApp()
class Viewer(BaseViewer):
    def __init__(self, filename, **kwargs):
        self._vtk_filename = filename[0] if len(filename) > 0 else None
        self._dataset_arrays = []
        self._draw_actors = []
        self._axes_actor = None
        self._scalarbar_actor = None
        state_defaults = {"colormap_idx": 0,
                          "lookuptable_idx": 1,
                          "active_ui": None,
                          }
        super().__init__(state_defaults=state_defaults, **kwargs)
        # self._server.state.setdefault("colormap_idx", 0)
        # self._server.state.setdefault("lookuptable_idx", 1)
        # self._server.state.setdefault("active_ui", None)

    @property
    def title(self):
        return self._server.state.trame__title + ': ' + \
            (self._vtk_filename if self._vtk_filename is not None else "")

    def generate_actors(self, renderer):
        if self._vtk_filename is None:
            return ()

        self._draw_actors = []
        mat2color = {
            "si":     self._colors.GetColor3d('Red'),
            "polysi": self._colors.GetColor3d('Blue'),
            "sio2":   self._colors.GetColor3d('Green'),
            "teos":   self._colors.GetColor3d('Pink'),
            "bpsg":   self._colors.GetColor3d('Violet'),
            "si3n4":  self._colors.GetColor3d('Yellow'),
            "al":     self._colors.GetColor3d('Silver'),
            "w":      self._colors.GetColor3d('Gold'),
        }

        ext = Path(self._vtk_filename).suffix
        if self.debug:
            print('file suffix is', ext.lower())
        readercls = READERCLASS.get(ext.lower(), None)
        if readercls is None:
            raise RuntimeError('Not found class for reading.')

        reader = readercls()
        # reader.DebugOn()  # 使えないらしい
        reader.SetFileName(self._vtk_filename)
        reader.Update()
        if reader.GetErrorCode() != 0:
            raise RuntimeError('Cannot open: ' + self._vtk_filename)

        data_obj = reader.GetOutput()
        if self.debug:
            print('date type is', type(data_obj))
        if data_obj is not None:
            data_obj.Register(reader)
        ds = vtkDataSet.SafeDownCast(data_obj)
        dc = vtkCompositeDataSet.SafeDownCast(data_obj)
        if self.debug:
            print('vtkDataSet is', ds is not None)
            print('vtkCompositeDataSet is', dc is not None)

        bounds = None

        if ds is not None:
            print("  number of cells:", ds.GetNumberOfCells())
            print("  number of points:", ds.GetNumberOfPoints())

            fields = [
                (ds.GetPointData(), vtkDataObject.FIELD_ASSOCIATION_POINTS),
                (ds.GetCellData(), vtkDataObject.FIELD_ASSOCIATION_CELLS),
            ]
            dataset_arrays = []
            for field in fields:
                field_arrays, association = field
                for i in range(field_arrays.GetNumberOfArrays()):
                    array = field_arrays.GetArray(i)
                    # print('array', array)
                    uc = vtkUnsignedCharArray.SafeDownCast(array)
                    # print('uc', uc)
                    dataset_arrays.append(
                        {"text": array.GetName(),
                         "variable_name": array.GetName(),
                         "value": i,
                         "range": list(array.GetRange()),
                         "type": association,
                         "u_char": uc is not None,
                         }
                    )
            # pprint(dataset_arrays)
            self._dataset_arrays = dataset_arrays

            # mapper = vtkPolyDataMapper()
            # vtkDataSetMapper は vtkDataSetSurfaceFilter + vtkPolyDataMapper
            # のようなもの、かな？
            # ref) Rendering/Core/vtkDataSetMapper.cxx
            mapper = vtkDataSetMapper()
            # mapper.DebugOn()  # こっちも使えないみたい
            # mapper.SetInputConnection(reader.GetOutputPort())
            mapper.SetInputData(ds)

            lut = mapper.GetLookupTable()
            # print(lut)

            # default (rainbow Red -> Blue)
            lut.SetHueRange(0.0, 0.66667)
            lut.SetSaturationRange(1, 1)
            lut.SetValueRange(1, 1)
            lut.SetAlphaRange(1, 1)
            lut.SetNumberOfColors(256)

            lut.Build()
            # mapper.SetLookupTable(lut)

            sb_actor = vtkScalarBarActor()
            sb_actor.SetLookupTable(lut)
            # sb_actor.SetNumberOfLabels(7)
            sb_actor.UnconstrainedFontSizeOn()
            sb_actor.SetMaximumWidthInPixels(100)
            sb_actor.SetMaximumHeightInPixels(800 // 3)
            # sb_actor.SetTitle("text")
            self._scalarbar_actor = sb_actor
            renderer.AddActor2D(sb_actor)

            actor = vtkActor()
            actor.SetMapper(mapper)
            prop = actor.GetProperty()
            prop.SetAmbient(0.1)
            prop.SetDiffuse(0.8)
            prop.SetSpecular(0.1)
            prop.SetColor(self._colors.GetColor3d('Black'))

            bounds = actor.GetBounds()
            if self.debug:
                print('   bounds:', bounds)

            self._draw_actors.append(actor)

        if dc is not None:
            print("  total of points:", dc.GetNumberOfPoints())
            defcolor = self._colors.GetColor3d('Black')
            compf = (min, max, min, max, min, max)

            iter = vtkDataObjectTreeIterator()
            iter.SetDataSet(dc)
            iter.SkipEmptyNodesOn()
            iter.VisitOnlyLeavesOn()
            iter.InitTraversal()
            while not iter.IsDoneWithTraversal():
                dso = iter.GetCurrentDataObject()
                ds = vtkDataSet.SafeDownCast(dso)
                info = iter.GetCurrentMetaData()
                if ds is None:
                    continue
                name = ""
                if info.Has(vtkCompositeDataSet.NAME()):
                    name = info.Get(vtkCompositeDataSet.NAME())
                if self.debug:
                    print(" data(#):", name)
                    print("   number of cells:", ds.GetNumberOfCells())
                    print("   number of points:", ds.GetNumberOfPoints())

                mapper = vtkDataSetMapper()
                mapper.SetInputData(ds)

                actor = vtkActor()
                actor.SetMapper(mapper)
                prop = actor.GetProperty()
                prop.SetAmbient(0.1)
                prop.SetDiffuse(0.8)
                prop.SetSpecular(0.1)

                if self.debug:
                    print('   color:', mat2color.get(name.lower(), defcolor))
                prop.SetColor(mat2color.get(name.lower(), defcolor))

                if bounds is None:
                    bounds = actor.GetBounds()
                else:
                    b = actor.GetBounds()
                    bounds = list(map(
                        lambda f, x, y: f(x, y), compf, bounds, b))

                self._draw_actors.append(actor)

                iter.GoToNextItem()

            if self.debug:
                print(' bounds:', bounds)

        self._dataset_arrays.append(
            {"text": '<solid>',
             "variable_name": '<solid>',
             "value": len(self._dataset_arrays),
             "range": [0, 255],
             "type": -1,
             "u_char": False,
             }
        )
        for i, arr in enumerate(self._dataset_arrays):
            self._dataset_arrays[i]["value"] = int(i)
        # pprint(self._dataset_arrays)

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

        axes = vtkCubeAxesActor()
        axes.SetUseTextActor3D(1)
        axes.SetBounds(bounds)
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
        # axes.SetFlyModeToClosestTriad()
        # axes.SetFlyModeToFurthestTriad()
        # axes.SetFlyModeToStaticTriad()
        # axes.SetFlyModeToStaticEdges()

        # print('Axes', axes)

        axes.SetCamera(renderer.GetActiveCamera())
        self._axes_actor = axes

        return *self._draw_actors, axes

    def _ui_card(self, title, ui_name):
        with vuetify.VCard(v_show=f"active_ui == '{ui_name}'"):
            '''
            vuetify.VCardTitle(
                title,
                classes="grey lighten-1 py-1 grey--text text--darken-3",
                style="user-select: none; cursor: pointer",
                hide_details=True,
                dense=True,
            )
            '''
            content = vuetify.VCardText(classes="py-2")
        return content

    @change("show_axes")
    def switch_show_axes(self, *args, **kwargs):
        if self._axes_actor is not None:
            sw = kwargs.get('show_axes', None)
            if type(sw) is bool:
                self._axes_actor.SetVisibility(sw)
                self.server.controller.update_views()  # 必要！

    @change("show_surface")
    def switch_show_surface(self, *args, **kwargs):
        # print('In switch_show_surface', kwargs.get('show_surface', None))
        sw = kwargs.get('show_surface', None)
        if type(sw) is not bool:
            return

        # for a in self.renderer.GetActors():
        for a in self._draw_actors:
            a.InitPathTraversal()
            # print(type(a), dir(a))
            while True:
                p = a.GetNextPath()
                if p is None:
                    break
                t = vtkActor.SafeDownCast(p.GetLastNode().GetViewProp())
                if t is None:
                    continue
                if sw:
                    t.GetProperty().SetRepresentationToSurface()
                else:
                    t.GetProperty().SetRepresentationToWireframe()

        # GetInteractor ()->Render ();
        self.server.controller.update_views()  # 必要！

    def setup_ui_in_layout_toolbar(self, toolbar):
        vuetify.VSpacer()
        vuetify.VSwitch(
            label='Surface',
            v_model=('show_surface', True),
            hide_details=True,
            dense=True,
        )
        vuetify.VSpacer()
        vuetify.VSwitch(
            label='Axes',
            v_model=('show_axes', True),
            hide_details=True,
            dense=True,
        )
        super().setup_ui_in_layout_toolbar(toolbar)

    @change("colormap_idx")
    def update_colormap_idx(self, *args, **kwargs):
        # print('update_colormap_idx', args)
        # pprint(kwargs)
        idx = kwargs.get('colormap_idx', -1)
        # print('idx', idx)
        if len(self._dataset_arrays) == 0:
            return
        arr = self._dataset_arrays[idx]
        type = arr.get("type")
        uc = arr.get("u_char", False)

        active_ui = "nothing"
        for actor in self._draw_actors:
            mapper = actor.GetMapper()
            if type < 0:
                mapper.ScalarVisibilityOff()
                self._scalarbar_actor.SetVisibility(False)
            else:
                mapper.ScalarVisibilityOn()
                mapper.SelectColorArray(arr.get("variable_name"))
                mapper.SetScalarRange(arr.get("range"))
                if type == vtkDataObject.FIELD_ASSOCIATION_POINTS:
                    mapper.SetScalarModeToUsePointFieldData()
                else:
                    mapper.SetScalarModeToUseCellFieldData()
                self._scalarbar_actor.SetVisibility(not uc)
                if not uc:
                    active_ui = "lut"
        self._server.state.active_ui = active_ui
        self.server.controller.update_views()

    @change("lookuptable_idx")
    def update_lookuptable_idx(self, *args, **kwargs):
        idx = kwargs.get('lookuptable_idx', -1)
        # print('update_lookuptable_idx', idx)

        lut = vtkLookupTable()
        # default, Rainbow (Red -> Blue)
        lut.SetHueRange(0.0, 0.66667)
        lut.SetSaturationRange(1, 1)
        lut.SetValueRange(1, 1)
        lut.SetAlphaRange(1, 1)
        lut.SetNumberOfColors(256)

        match idx:
            case 1:  # rainbow Blue -> Red
                lut.SetHueRange(0.66667, 0.0)

            case 2:  # gray scale
                lut.SetHueRange(0, 0)
                lut.SetSaturationRange(0, 0)
                lut.SetValueRange(0.2, 1.0)

            case 3:  # Custom
                lut.SetNumberOfColors(20)
                lut.Build()

                colors = self._colors
                lut.SetTableValue(0, colors.GetColor4d("red"))
                lut.SetTableValue(1, colors.GetColor4d("lime"))
                lut.SetTableValue(2, colors.GetColor4d("yellow"))
                lut.SetTableValue(3, colors.GetColor4d("blue"))
                lut.SetTableValue(4, colors.GetColor4d("magenta"))
                lut.SetTableValue(5, colors.GetColor4d("cyan"))
                lut.SetTableValue(6, colors.GetColor4d("spring_green"))
                lut.SetTableValue(7, colors.GetColor4d("lavender"))
                lut.SetTableValue(8, colors.GetColor4d("mint_cream"))
                lut.SetTableValue(9, colors.GetColor4d("violet"))
                lut.SetTableValue(10, colors.GetColor4d("ivory_black"))
                lut.SetTableValue(11, colors.GetColor4d("coral"))
                lut.SetTableValue(12, colors.GetColor4d("pink"))
                lut.SetTableValue(13, colors.GetColor4d("salmon"))
                lut.SetTableValue(14, colors.GetColor4d("sepia"))
                lut.SetTableValue(15, colors.GetColor4d("carrot"))
                lut.SetTableValue(16, colors.GetColor4d("gold"))
                lut.SetTableValue(17, colors.GetColor4d("forest_green"))
                lut.SetTableValue(18, colors.GetColor4d("turquoise"))
                lut.SetTableValue(19, colors.GetColor4d("plum"))

        lut.Build()
        for actor in self._draw_actors:
            mapper = actor.GetMapper()
            mapper.SetLookupTable(lut)
        self._scalarbar_actor.SetLookupTable(lut)
        self.server.controller.update_views()

    def setup_ui_in_layout_drawer(self, drawer):
        drawer.width = 175
        with vuetify.VRow(classes="pt-2", dense=True):
            with vuetify.VCol(cols="12"):
                vuetify.VSelect(
                    label="Select",
                    v_model=("colormap_idx", 0),
                    items=("colormap_list", self._dataset_arrays),
                    hide_details=True,
                    dense=True,
                    outlined=True,
                    classes="pt-1",
                )
                _arrays = [
                    {"text": "Rainbow (Red -> Blue)", "value": 0},
                    {"text": "Rainbow (Blue -> Red)", "value": 1},
                    {"text": "Grayscale", "value": 2},
                    {"text": "Custom", "value": 3},
                ]
                with self._ui_card(title="Lookup Table", ui_name="lut"):
                    vuetify.VSelect(
                        label="Select lookup-table",
                        v_model=("lookuptable_idx", 1),
                        items=("lookuptable_list", _arrays),
                        hide_details=True,
                        dense=True,
                        outlined=True,
                        classes="pt-1",
                    )


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
