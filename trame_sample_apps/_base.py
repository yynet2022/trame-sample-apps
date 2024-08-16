#
from inspect import signature  # noqa
from pprint import pprint  # noqa

from trame.app import get_server
from trame.widgets import vuetify, vtk as vtk_widgets
from trame.ui.vuetify import SinglePageLayout
from trame.decorators import change

from vtkmodules.vtkRenderingCore import (
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)
from vtkmodules.vtkCommonTransforms import (
    vtkPerspectiveTransform,
)
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch  # noqa
from vtkmodules.vtkCommonColor import vtkNamedColors


VTK_VIEW_SCALE_INFO = {
    "default": 1.0,
    "min": 0.1,
    "max": 3.0,
    "step": 0.1,
}

VTK_VIEW_SETTINGS = {
    "interactive_ratio": 1,
    "interactive_quality": 100,
}

VTK_VIEW_EVENTS = [
    "StartAnimation",
    "Animation",
    "EndAnimation",
    "MouseEnter",
    "MouseLeave",
    "StartMouseMove",
    "MouseMove",
    "EndMouseMove",
    "LeftButtonPress",
    "LeftButtonRelease",
    "MiddleButtonPress",
    "MiddleButtonRelease",
    "RightButtonPress",
    "RightButtonRelease",
    "KeyPress",
    "KeyDown",
    "KeyUp",
    "StartMouseWheel",
    "MouseWheel",
    "EndMouseWheel",
    "StartPinch",
    "Pinch",
    "EndPinch",
    "StartPan",
    "Pan",
    "EndPan",
    "StartRotate",
    "Rotate",
    "EndRotate",
    "Button3D",
    "Move3D",
    "StartPointerLock",
    "EndPointerLock",
    "StartInteraction",
    "Interaction",
    "EndInteraction",
]


def on_event(*args, **kwargs):
    print("In on_event", args, kwargs)


def event_listeners(events):
    result = {}
    for event in events:
        result[event] = (on_event, "[utils.vtk.event($event)]")
    return result


def printCameraInfo(camera):
    # print(dir(camera))
    # print('poll', camera.GetRoll())
    # print('windowcenter', camera.GetWindowCenter())
    _params = dict(
        position=camera.GetPosition(),
        distance=camera.GetDistance(),
        focalPoint=camera.GetFocalPoint(),
        focalDistance=camera.GetFocalDistance(),
        viewUp=camera.GetViewUp(),
        parallelProjection=camera.GetParallelProjection(),
        parallelScale=camera.GetParallelScale(),
        viewAngle=camera.GetViewAngle(),
        eyeAngle=camera.GetEyeAngle(),
    )
    pprint(_params)


def rotateCamera(camera, angles, fc=None, rd=None):
    if fc is None:
        fc = camera.GetFocalPoint()
    if rd is None:
        rd = camera.GetDistance()

    t = vtkPerspectiveTransform()
    t.Identity()
    t.Translate(+fc[0], +fc[1], +fc[2])
    t.RotateWXYZ(angles[0], 1.0, 0.0, 0.0)
    t.RotateWXYZ(angles[1], 0.0, 1.0, 0.0)
    t.RotateWXYZ(angles[2], 0.0, 0.0, 1.0)
    t.Translate(-fc[0], -fc[1], -fc[2])

    pos = (fc[0], fc[1], fc[2] + rd)
    w = [0]*3
    t.TransformPoint(pos, w)
    camera.SetPosition(w)
    # print('pos', w)

    vpos = (fc[0], fc[1] + 1.0, fc[2])
    t.TransformPoint(vpos, w)
    camera.SetViewUp(w[0] - fc[0], w[1] - fc[1], w[2] - fc[2])
    # print('vew', w[0] - fc[0], w[1] - fc[1], w[2] - fc[2])

    camera.OrthogonalizeViewUp()


def initCamera(renderer, prop0):
    """
    prop0 = {
        'focalPoint': ...,
        'distance': ...,
        'parallelScale': ...,
        'viewAngle': ...,
    }
    """

    renderer.ResetCamera()
    renderer.ResetCameraClippingRange()

    camera = renderer.GetActiveCamera()
    camera.ParallelProjectionOn()
    # printCameraInfo(camera)

    camera.SetParallelScale(prop0['parallelScale'])
    camera.SetViewAngle(prop0['viewAngle'])
    rotateCamera(camera, (60.0, -20.0, 0.0),
                 prop0['focalPoint'], prop0['distance'])
    # camera.Zoom(1.0)
    # printCameraInfo(camera)


class myView(vtk_widgets.VtkLocalView):
    def __init__(self, view, **kwargs):
        super().__init__(view, **kwargs)

    def update(self, *args, **kwargs):
        # print('In update')
        super().update(*args, **kwargs)

    def reset_camera(self, *args, **kwargs):
        # print('In reset_camera')
        super().reset_camera(*args, **kwargs)

    def push_camera(self, *args, **kwargs):
        # print('In push_camera')
        super().push_camera(*args, **kwargs)


class BaseViewer:
    def __init__(self, server_or_name=None, title="VTK Viewer",
                 client_type="vue2", **kwargs):
        self._debug = kwargs.get('debug', False)

        self._server = get_server(server_or_name, client_type=client_type)
        # self.state, self.ctrl = self._server.state, self._server.controller
        self._server.controller.on_server_ready.add(self.on_ready)

        self._server.state.trame__title = title

        self._colors = vtkNamedColors()
        cp = map(lambda x: x / 255.0, [0, 255, 255, 255])
        self._colors.SetColor("TestColor", *cp)

        self._vtk_rw = self._vtk_setup()
        self._ui = self._setup_ui()

    @property
    def server(self):
        return self._server

    @property
    def title(self):
        return self._server.state.trame__title

    @property
    def debug(self):
        return self._debug

    def get_actors(self, renderer):
        return ()

    def _vtk_setup(self):
        renderer = vtkRenderer()
        renderer.SetBackground(self._colors.GetColor3d('White'))

        for x in self.get_actors(renderer):
            renderer.AddActor(x)

        # ResetCamera()はしておく
        renderer.ResetCamera()
        camera = renderer.GetActiveCamera()

        if self.debug:
            print('def ParallelScale:', camera.GetParallelScale())
        self._camera_prop0 = {
            'focalPoint': camera.GetFocalPoint(),
            'distance': camera.GetDistance(),
            'parallelScale': camera.GetParallelScale()*1.05,
            'viewAngle': 30.0,
        }
        if self.debug:
            print('camera prop0 =')
            pprint(self._camera_prop0)

        initCamera(renderer, self._camera_prop0)
        # printCameraInfo(renderer.GetActiveCamera())

        renderWindow = vtkRenderWindow()
        renderWindow.AddRenderer(renderer)
        renderWindow.OffScreenRenderingOn()

        renderWindowInteractor = vtkRenderWindowInteractor()
        renderWindowInteractor.SetRenderWindow(renderWindow)
        renderWindowInteractor.GetInteractorStyle() \
                              .SetCurrentStyleToTrackballCamera()

        renderWindow.Render()
        return renderWindow

    def push_camera(self):
        self._push_camera(
            self._vtk_rw.GetRenderers().GetFirstRenderer().GetActiveCamera())

    @change("scale")
    def update_scale(self, scale=-1, **kwargs):
        # print('update_scale> ', scale)
        ps = self._camera_prop0['parallelScale'] / scale
        for r in self._vtk_rw.GetRenderers():
            r.GetActiveCamera().SetParallelScale(ps)
        self.push_camera()
        self.server.controller.update_views()
        # printCameraInfo(renderer.GetActiveCamera())

    def update_reset_scale(self):
        self.server.state.scale = VTK_VIEW_SCALE_INFO['default']
        # print('update_reset_scale> ', self.server.state.scale)
        s = self._camera_prop0['parallelScale'] / self.server.state.scale
        for r in self._vtk_rw.GetRenderers():
            r.GetActiveCamera().SetParallelScale(s)
        self.push_camera()
        self.server.controller.update_views()

    def do_icon_click(self, ev, camera_props, *a, **k):
        # print("do_icon_click", ev, a, k)
        # pprint(camera_props)

        self.server.state.scale = VTK_VIEW_SCALE_INFO['default']
        for x in self._vtk_rw.GetRenderers():
            initCamera(x, self._camera_prop0)
        # printCameraInfo(
        #     self._vtk_rw.GetRenderers().GetFirstRenderer().GetActiveCamera())
        self.push_camera()
        # self._vtk_rw.Render()
        self.server.controller.update_views()
        # self.server.controller.reset_camera()

    def on_ready(self, *a, **k):
        # print('on_ready', a)
        # pprint(k)
        pass

    def on_right_button_release(self, pickData):
        # print('on_right', pickData)
        pass

    def on_end_animation(self, camera_info):
        # print('on_end_animation')
        # pprint(camera_info)
        # print()

        do_push = False
        s = camera_info.get("parallelScale")
        scale = self._camera_prop0['parallelScale'] / s
        if scale < VTK_VIEW_SCALE_INFO['min']:
            scale = VTK_VIEW_SCALE_INFO['min']
            s = self._camera_prop0['parallelScale'] / scale
            do_push = True
        if scale > VTK_VIEW_SCALE_INFO['max']:
            scale = VTK_VIEW_SCALE_INFO['max']
            s = self._camera_prop0['parallelScale'] / scale
            do_push = True

        # Synchronize cameras
        for r in self._vtk_rw.GetRenderers():
            camera = r.GetActiveCamera()
            camera.SetPosition(camera_info.get("position"))
            camera.SetFocalPoint(camera_info.get("focalPoint"))
            camera.SetViewUp(camera_info.get("viewUp"))
            camera.SetViewAngle(camera_info.get("viewAngle"))
            camera.SetParallelProjection(camera_info.get("parallelProjection"))
            camera.SetParallelScale(s)

        if do_push:
            self.push_camera()
            self.server.controller.update_views()
        self.server.state.scale = scale

    def _setup_ui(self):
        with SinglePageLayout(self.server) as layout:
            layout.icon.click = (
                self.do_icon_click,
                "[utils.vtk.event($event), $refs.view.getCamera()]")
            layout.title.set_text(self.title)

            with layout.toolbar:
                vuetify.VSpacer()
                vuetify.VSlider(
                    v_model=("scale", VTK_VIEW_SCALE_INFO['default']),
                    min=VTK_VIEW_SCALE_INFO['min'],
                    max=VTK_VIEW_SCALE_INFO['max'],
                    step=VTK_VIEW_SCALE_INFO['step'],
                    hide_details=True,
                    dense=True,
                    style="max-width: 300px",
                )
                vuetify.VDivider(vertical=True, classes="mx-2")
                with vuetify.VBtn(icon=True, click=self.update_reset_scale):
                    vuetify.VIcon("mdi-undo-variant")

            with layout.content:
                with vuetify.VContainer(
                        fluid=True,
                        classes="pa-0 fill-height",
                ):
                    view = myView(
                        self._vtk_rw, ref="view",
                        interactor_events=(
                            "events",
                            ["RightButtonRelease",
                             "EndAnimation",
                             ],
                        ),
                        RightButtonRelease=(
                            self.on_right_button_release,
                            "[utils.vtk.event($event)]",
                        ),
                        EndAnimation=(
                            self.on_end_animation,
                            "[$event.pokedRenderer.getActiveCamera().get()]",
                        ),
                        # interactor_events=("event_types", VTK_VIEW_EVENTS),
                        # **event_listeners(VTK_VIEW_EVENTS),
                        **VTK_VIEW_SETTINGS,
                    )
                    self.server.controller.update_views.add(view.update)
                    self.server.controller.reset_camera.add(view.reset_camera)
                    self._push_camera = view.push_camera

            return layout
