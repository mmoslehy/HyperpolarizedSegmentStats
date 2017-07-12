# Works with 3D Slicer to extract 4D data from segmented DICOMs :cake:

## USAGE:

### Slicer.exe --python-script main.py [args] [--exit-after-startup]

#### **_args:_**

| Argument					| Type				| Optional	|
| ------------------------- |:-----------------:|:---------:|
| --foldersavename			| Name				| No		|
| --segmentationfile		| Path				| No		|
| --pathtodicoms			| Path				| No		|
| --keepnrrddir				| Boolean			| Yes		|
| --excludedirs\*			| Name				| Yes		|
| --getsnr					| SegmentName		| Yes		|
| --denominatormetabolite	| Name				| Yes		|
| --hiderawsheets			| boolean			| Yes		|

_\*Can be a list of names_