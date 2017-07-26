import os, sys, logging
from argumentparser import ArgumentParser, ArgumentError
import statscollector
## Debugging
def dbg():
	import ptvsd
	ptvsd.enable_attach(secret='s')
	ptvsd.wait_for_attach()

# Uncomment this line to enable debugging in Visual Studio
# dbg()
## End debug


argParser = ArgumentParser(sys.argv)
try:
	argParser.ValidateAllArgs()
except ArgumentError as err:
	logging.error("\nERROR: " + err.message)
	logging.error(argParser.GetUsage())

# Otherwise, store the pathname provided as an argument
else:
	# Assume the Dicom To Nrrd Converter is in the same folder as this script
	pathtoconverter = os.path.join(os.path.split(sys.argv[0])[0], "DicomToNrrdConverter.exe")
	# Get parsed arguments
	pathtodicoms = argParser.GetArg("pathtodicoms")[0]
	segmentationfile = argParser.GetArg("segmentationfile")[0]
	foldersaveName = argParser.GetArg("foldersavename")[0]
	keepnrrddir = argParser.GetArg("keepnrrddir")
	snrsegment = argParser.GetArg("getsnr")[0]
	denominatormetabolite = argParser.GetArg("denominatormetabolite")[0]
	excludedirs = argParser.GetArg("excludedirs")
	hiderawsheets = argParser.GetArg("hiderawsheets")
	me = statscollector.MetaExporter(pathtodicoms, pathtoconverter, segmentationfile, foldersaveName, keepnrrddir, snrsegment, denominatormetabolite, excludedirs, hiderawsheets)