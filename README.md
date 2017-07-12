Works with 3D Slicer to extract 4D data from segmented DICOMs

USAGE:

Slicer.exe --python-script main.py [args] [--exit-after-startup]

possible args:
--foldersavename ['name']
--hiderawsheets ['boolean'] (optional)
--segmentationfile ['path']
--keepnrrddir ['boolean'] (optional)
--excludedirs ['name'] (optional)
--denominatormetabolite ['name', 'dcmFolder'] (optional)
--pathtodicoms ['path']
--getsnr ['segmentName'] (optional)