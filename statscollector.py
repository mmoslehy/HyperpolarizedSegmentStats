import vtkSegmentationCorePython as vtkSegmentationCore
import vtkSlicerSegmentationsModuleLogicPython as vtkSlicerSegmentationsModuleLogic
import slicer, logging, os, shutil
from SegmentStatistics import SegmentStatisticsLogic
import openpyxl

#--DEBUGGING--
#import ptvsd
#ptvsd.enable_attach(secret='slicer')
#ptvsd.wait_for_attach()
# -----------

"""This script assumes that the number of volumes (time points) for all metabolites are the same"""

class NrrdConverterLogic(object):

	# Constructor for the DicomToNrrdConverter
	def __init__(self, pathToDicoms, pathToConverter):
		self.pathToDicoms = os.path.normpath(pathToDicoms)
		self.converter = os.path.normpath(pathToConverter)
		if not os.path.exists(self.pathToDicoms) or not os.path.exists(self.converter):
			print("DICOMs or DicomToNrrdConverter.exe does not exist")
			quit()

	# Loop through directory given to find directories with .dcm files, return a list of those directory paths
	def getDicomDirs(self):
		pathWalk = os.walk(self.pathToDicoms)
		dicomDirs = []
		for root, dirs, files in pathWalk:
			for file in files:
				if file.lower().endswith(".dcm") or file.lower().endswith(".ima"):
					dicomDirs.append(root)
		# Remove duplicates
		noDuplicates = list(set(dicomDirs))
		# Sort the list
		noDuplicates.sort()
		return noDuplicates

	# Convert all DICOMs to Nrrd files with the names of their respective DICOM directories
	def convertToNrrd(self):
		dicomDirs = self.getDicomDirs()
		condDictionary = {}
		dcmDictionary = {}
		for dicomDir in dicomDirs:
			# Specify the output nrrd file name
			nrrdFile = os.path.split(dicomDir)[1]
			# Get the full path of the metabolite folder and its parent
			metaboliteDirPath = os.path.split(os.path.split(dicomDir)[0])
			# This is the directory above the directory containing the DICOMs (e.g. if pyrBy6/8001/x.dcm then this is PyBy6)
			metaboliteDirName = metaboliteDirPath[1]
			# Get the directory name above the metabolite directory (e.g. 100percentOxygen)
			conditionDir = os.path.split(metaboliteDirPath[0])[1]
			# Directory to hold Nrrd files
			documentsDir = os.path.normpath(os.path.expanduser(r"~\\Documents\\StatsCollector\\NrrdOutput"))
			if not os.path.exists(documentsDir):
				os.makedirs(documentsDir)
			# Parent folder name holding the Nrrd files, will be used to specify the CSV file names
			parentFolder = conditionDir + "-" + metaboliteDirName
			# Nrrd file path
			outputFilePath = os.path.normpath(documentsDir + "\\" + parentFolder + "_" + nrrdFile + ".nrrd")
			runnerPath = os.path.split(self.converter)[0] + '\\runner.bat'
			execString = runnerPath + " " + self.converter + " --inputDicomDirectory " + dicomDir + " --outputVolume " + outputFilePath
			# Use DicomToNrrdConverter.exe to convert all DICOMs, inserting their output file paths into a dictionary to return after execution, supress stdout of converter
			os.system(execString + " > nul")

			key = conditionDir

			# Append nrrd file names to dictionary
			if not dcmDictionary.has_key(key):
				dcmDictionary[key] = {}
			
			if not dcmDictionary[key].has_key(metaboliteDirName):
				dcmDictionary[key][metaboliteDirName] = []

			dcmDictionary[key][metaboliteDirName].append(outputFilePath)
			

			# Inform the user that the DICOMs were successfully converted
			logging.info("Successfully converted DICOMs in " + parentFolder)
		return dcmDictionary

class StatsCollectorLogic(object):
	# Constructor to store the segmentation file name in the object's attributes
	def __init__(self, segmentationFile, noiseSegment):
		self.segFile = os.path.normpath(segmentationFile)
		self.segNode = slicer.util.loadSegmentation(self.segFile,returnNode=True)[1]
		self.xlWorkbooks = {}
		self.noiseSegment = noiseSegment
		self.metaStats = {}
		# See whether to get SNRs
		self.getsnr = len(self.noiseSegment) != 0
		if self.getsnr:
			seg = self.segNode.GetSegmentation()
			for i in range(seg.GetNumberOfSegments()):
				if seg.GetNthSegment(i).GetName() == self.noiseSegment:
					self.noiseSegmentID = seg.GetNthSegmentID(i)

	# Function to check if a string is a float
	@staticmethod
	def digitize(s):
		try:
			return float(s)
		except ValueError:
			return s

	def computeSnrs(self, segStatLogic, segmentIDs, noiseStdev):
		for segmentID in segmentIDs:
			segStatLogic.statistics[segmentID, "SNR"] = segStatLogic.statistics[segmentID, "GS mean"] / noiseStdev
		return segStatLogic

	# Gets sheet
	def getWorkSheet(self, workbook, sheetName):
		existingSheetNames = workbook.get_sheet_names()
		existingSheetNames = [x.encode('UTF8') for x in existingSheetNames]

		if sheetName in existingSheetNames:
			return workbook.get_sheet_by_name(sheetName)
		else:
			return workbook.create_sheet(sheetName)

	# Make worksheets for raw signal, SNR, and SNR ratio relative to a specific denominator (e.g. the metabolite pyruvate)
	def advancedData(self, denominatorMetabolite):
		seg = self.segNode.GetSegmentation()
		segNames = [seg.GetNthSegment(segIndex).GetName() for segIndex in range(seg.GetNumberOfSegments())]
		segNames.remove(self.noiseSegment)
		for wbPath, wb in self.xlWorkbooks.items():
			rawSignalWs = self.getWorkSheet(wb, "Raw Signal")
			snrSignalWs = self.getWorkSheet(wb, "SNR")
			ratioWs = self.getWorkSheet(wb, "Ratios")
			condition = os.path.basename(wbPath).rstrip('.xlsx')
			denominatorMetaboliteSeries = self.metaStats[condition][denominatorMetabolite]
			for seriesName, series in self.metaStats[condition].items():
				rawSignalWs.append([seriesName])
				rawSignalWs.append([''] + segNames + ['BG STDEV'])
				snrSignalWs.append([seriesName])
				snrSignalWs.append([''] + segNames)
				if seriesName != denominatorMetabolite:
					ratioWs.append([seriesName])
					ratioWs.append([''] + segNames)
				for i in range(len(series)):
					rawRow = [i + 1]
					snrRow = [i + 1]
					ratioRow = [i + 1]

					stats = series[i].statistics
					for segmentID in stats["SegmentIDs"]:
						if segmentID != self.noiseSegmentID:
							rawRow += [stats[segmentID, "GS mean"]]
							snrRow += [stats[segmentID, "SNR"]]
							if seriesName != denominatorMetabolite:
								ratioRow += [stats[segmentID, "SNR"] / denominatorMetaboliteSeries[i].statistics[segmentID, "SNR"]]
					rawRow += [stats[self.noiseSegmentID, "GS stdev"]]
					rawSignalWs.append(rawRow)
					snrSignalWs.append(snrRow)
					if seriesName != denominatorMetabolite:
						ratioWs.append(ratioRow)

	def getWorkBook(self, workbookName):
		if not self.xlWorkbooks.has_key(workbookName):
			self.xlWorkbooks[workbookName] = openpyxl.Workbook()
		return self.xlWorkbooks[workbookName]

	def exportStatsToXl(self, segStatLogic, xlsxFileName, header="", sheetName=""):
		outputFile = xlsxFileName
		if not xlsxFileName.lower().endswith('.xlsx'):
			outputFile += '.xlsx'

		wb = self.getWorkBook(outputFile)

		stats = segStatLogic.exportToString()
		rows = stats.split('\n')

		ws = self.getWorkSheet(wb, sheetName)

		ws.append([header])
		columnTitles = rows[0].split(',')
		ws.append(columnTitles)

		for row in rows[1:]:
			items = row.split(',')
			items[:] = [self.digitize(x) for x in items]
			ws.append(items)

	# Get statistics for a specific volume/timepoint
	def getStatForVol(self, volFile, folderSaveName, condition, seriesName=""):
		# Load master volumes
		vol = slicer.util.loadVolume(volFile, returnNode=True)

		if not vol[0]:
			# Print error if volume does not exist or is inaccessible
			print("Volume could not be loaded from: " + volFile)
			quit()

		volNode = vol[1]

		# Compute statistics
		segStatLogic = SegmentStatisticsLogic()
		segStatLogic.computeStatistics(self.segNode, volNode)

		if self.getsnr:
			noiseStdev = segStatLogic.statistics[self.noiseSegmentID, "GS stdev"]
			segStatLogic = self.computeSnrs(segStatLogic, segStatLogic.statistics['SegmentIDs'], noiseStdev)

		if seriesName not in self.metaStats[condition]:
			self.metaStats[condition][seriesName] = []

		# Append current volume's statistics to the statistics database
		self.metaStats[condition][seriesName].append(segStatLogic)

		# Specify the file name/path
		documentsDir = os.path.normpath(os.path.expanduser(r"~\\Documents\\StatsCollector\\SegmentStatistics"))
		filePath = os.path.join(documentsDir, folderSaveName, condition)
		fileParentDir = os.path.split(filePath)[0]

		# Make the SegmentStatistics directory if it does not exist
		if not os.path.exists(fileParentDir):
			os.makedirs(fileParentDir)

		# Export the stats to a file
		self.exportStatsToXl(segStatLogic, filePath, volNode.GetName(), seriesName)

class MetaExporter(object):
	def __init__(self, pathToDicoms, pathToConverter, segmentationFile, folderSaveName, keepNrrdDir, noiseSegment, denominatorMetabolite):
		self.converter = NrrdConverterLogic(pathToDicoms, pathToConverter)
		self.sc = StatsCollectorLogic(segmentationFile, noiseSegment)
		self.folderSaveName = folderSaveName
		if len(denominatorMetabolite) == 0:
			self.denominatorMetabolite = "01_pyrBy6"
		else:
			self.denominatorMetabolite = denominatorMetabolite

		# Get all stats
		dcmDictionary = self.converter.convertToNrrd()
		
		for condition, conditionDict in dcmDictionary.items():
			if not condition in self.sc.metaStats:
				self.sc.metaStats[condition] = {}
			for metabolite, volumes in conditionDict.items():
				for volume in volumes:
					saveName = os.path.join(self.folderSaveName, condition)
					self.sc.getStatForVol(volume, self.folderSaveName, condition, metabolite)

		# Export stats to XLSX files
		self.sc.advancedData(self.denominatorMetabolite)
		for wbName, wb in self.sc.xlWorkbooks.items():
			wb.remove_sheet(wb.worksheets[0])
			wb.save(wbName)

		# Delete the NrrdOutput directory by default
		if not keepNrrdDir:
			shutil.rmtree(os.path.normpath(os.path.expanduser(r"~\\Documents\\StatsCollector\\NrrdOutput")))
