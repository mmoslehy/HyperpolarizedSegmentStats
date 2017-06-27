import os, sys, logging
from argumentparser import ArgumentParser, ArgumentError
import statscollector
#Debugging
# import ptvsd
# ptvsd.enable_attach(secret='s')
# ptvsd.wait_for_attach()
#End debug


argParser = ArgumentParser(sys.argv)
try:
	argParser.ValidateAllArgs()
except ArgumentError as err:
	logging.error("ERROR: " + err.message)
	logging.error(argParser.GetUsage())

# Otherwise, store the pathname provided as an argument
else:
	# Assume the Dicom To Nrrd Converter is in the same folder as this script
	pathToConverter = os.path.join(os.path.split(sys.argv[0])[0], "DicomToNrrdConverter.exe")
	# Get parsed arguments
	pathToDicoms = argParser.GetArg("pathtodicoms")[0]
	segmentationFile = argParser.GetArg("segmentationfile")[0]
	folderSaveName = argParser.GetArg("foldersavename")[0]
	keepNrrdDir = argParser.GetArg("keepnrrddir")
	snrSegment = argParser.GetArg("getsnr")[0]

	me = statscollector.MetaExporter(pathToDicoms, pathToConverter, segmentationFile, folderSaveName, keepNrrdDir, snrSegment)