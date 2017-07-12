# Works with 3D Slicer to extract 4D data from segmented DICOMs :cake:

## USAGE:

### Slicer.exe --python-script main.py [args] [--exit-after-startup]

#### **_args:_**

- --foldersavename ['name']
- --segmentationfile ['path']
- --pathtodicoms ['path']
- --keepnrrddir ['boolean'] *(optional)*
- --excludedirs ['name'] *(optional)*
   
   *This can be a list of names*
- --getsnr ['segmentName'] *(optional)*
- --denominatormetabolite ['name', 'dcmFolder'] *(optional)*
- --hiderawsheets ['boolean'] *(optional)*