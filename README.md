# trame-sample-apps
My sample WebApp by trame

## Requirements
```bash
pip install vtk trame trame-vtk trame-vuetify
```

### My environment (2024/8/17)
- Windows         11 home 23H2
- Python          3.12.5
- vtk             9.3.1
- trame           3.6.3
- trame-vtk       2.8.10
- trame-vtk       2.8.10
- trame-vuetify   2.6.2


## Installation
```bash
pip install -e .
```

or packaging:
1. install pip, setuptools, wheel, build
2. check setup.cfg & setup.py
3. python -m build

## Run
```bash
python -m trame_sample_apps.app1
python -m trame_sample_apps.app2 a.vtk
python -m trame_sample_apps.app2 c.vtp
(a.vtk and c.vtp in trame_sample_apps/data/)
```

## License
This is under [MIT license](https://en.wikipedia.org/wiki/MIT_License).


## Patch
For trame-vtk  2.8.10
It seems that remote camera information (parallelProjection, ...) is not shared locally during the initial stage of program startup.

```bash
--- trame_vtk.org/modules/vtk/serializers/render_windows.py	2024-08-14 11:50:20.770132700 +0900
+++ trame_vtk/modules/vtk/serializers/render_windows.py	2024-08-15 17:11:33.746290500 +0900
@@ -96,6 +96,9 @@
             "position": instance.GetPosition(),
             "viewUp": instance.GetViewUp(),
             "clippingRange": instance.GetClippingRange(),
+            "parallelProjection": instance.GetParallelProjection(),
+            "parallelScale": instance.GetParallelScale(),
+            "viewAngle": instance.GetViewAngle(),
         },
     }
 
```


Thank you!
