# Works with 3D Slicer to extract 4D data from segmented DICOMs :cake:

## USAGE:

### Slicer.exe --python-script main.py [args] [--exit-after-startup]

#### **_args:_**
<!-- 
- --foldersavename ['name']
- --segmentationfile ['path']
- --pathtodicoms ['path']
- --keepnrrddir ['boolean'] *(optional)*
- --excludedirs ['name'] *(optional)*
   
   *This can be a list of names*
- --getsnr ['segmentName'] *(optional)*
- --denominatormetabolite ['name', 'dcmFolder'] *(optional)*
- --hiderawsheets ['boolean'] *(optional)* -->

| Argument					| Type				| Optional	|
| ------------------------- |:-----------------:|:---------:|
| --foldersavename			| Name				| No		|
| --segmentationfile		| Path				| No		|
| --pathtodicoms			| Path				| No		|
| --keepnrrddir				| Boolean			| Yes		|
| --excludedirs\*				| Name				| Yes		|
| --getsnr					| SegmentName		| Yes		|
| --denominatormetabolite	| Name				| Yes		|
| --hiderawsheets			| boolean			| Yes		|

**\*_Can be a list of names_**