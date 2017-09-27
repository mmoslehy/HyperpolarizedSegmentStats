# Works with 3D Slicer to extract 4D data from segmented DICOMs :cake:
###### Currently only supported in Windows

## Instructions:
- [Download and install Slicer 4.7 or newer (currently the Nightly Build)](http://download.slicer.org/)
- [Download and install Git Bash (press next all the way through)](https://git-scm.com/downloads)
- Run Git Bash and execute the following command:
	`git clone https://github.com/moselhy/HyperpolarizedSegmentStats`
The script will be at `%USERPROFILE%\HyperpolarizedSegmentStats`
- From Command Prompt, run the script using Slicer's `--python-script` argument (see [example](#example))


*If you want Slicer to exit after the script is done execution, also use Slicer's `--exit-after-startup` argument*


**The script will save all the data in `%USERPROFILE%\Documents\StatsCollector`**

## Usage:

### `Slicer.exe --python-script %USERPROFILE%\HyperpolarizedSegmentStats\main.py args [--exit-after-startup]`

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
| --csv						| boolean			|

_\*are required_

_\*\*can be a list of names_

## Example:

From Command Prompt, run:

`"C:\Program Files\Slicer 4.7.0-2017-07-10\Slicer.exe" --python-script "%USERPROFILE%\HyperpolarizedSegmentStats\main.py" --pathtodicoms "%USERPROFILE%\HyperpolarizedSegmentStats\sampledata" --segmentationfile "%USERPROFILE%\HyperpolarizedSegmentStats\sampledata\Segmentation.seg.nrrd" --foldersavename 54657_stats --getsnr BACKGROUND --excludedirs Ser06_T1 Ser10_T2 --exit-after-startup`