# Works with 3D Slicer to extract 4D data from segmented DICOMs :cake:
###### Currently only supported in Windows

## Instructions:
- [Download and install Slicer 4.7 or newer (Currently the Nightly Build)](https://download.slicer.org/)
- [Download and install Git Bash (press next all the way through)](https://git-scm.com/downloads)
- Run Git Bash and execute the following command:
	`git clone https://github.com/mmoslehy/HyperpolarizedSegmentStats`
- The script will be at `%USERPROFILE%\HyperpolarizedSegmentStats`

## USAGE:

### `Slicer.exe --python-script main.py [args] [--exit-after-startup]`

#### **_args:_**

| Argument					| Type				|
| ------------------------- | ----------------- |
| --foldersavename\*		| Name				|
| --segmentationfile\*		| Path				|
| --pathtodicoms\*			| Path				|
| --keepnrrddir				| Boolean			|
| --excludedirs\*\*			| Name				|
| --getsnr					| SegmentName		|
| --denominatormetabolite	| Name				|
| --hiderawsheets			| boolean			|

_\*are required_
_\*\*can be a list of names_

## Example:

`"C:\Program Files\Slicer 4.7.0-2017-07-10\Slicer.exe" --python-script "%USERPROFILE%\HyperpolarizedSegmentStats\main.py" --pathtodicoms "%USERPROFILE%\HyperpolarizedSegmentStats\sampledata" --segmentationfile "%USERPROFILE%\HyperpolarizedSegmentStats\sampledata\Segmentation.seg.nrrd" --foldersavename 54657_stats --getsnr BACKGROUND --excludedirs Ser06_T1 Ser10_T2 --exit-after-startup`