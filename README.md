# trame-sample-apps
My sample WebApp by trame

## Requirements
```bash
pip install vtk trame trame-vtk trame-vuetify
```

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
(a.vtk in data/)
```

## License
This is under [MIT license](https://en.wikipedia.org/wiki/MIT_License).


## Patch
For trame-vtk  2.8.10

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
