import vtkSegmentationCorePython as vtkSegmentationCore
import vtkSlicerSegmentationsModuleLogicPython as vtkSlicerSegmentationsModuleLogic
import slicer, logging, os, shutil
from SegmentStatistics import SegmentStatisticsLogic
import openpyxl

"""
By: Mohamed Moselhy (Western University), 2017
Uses 3DSlicer's SegmentStatistics module to extract data from hyperpolarized Carbon-13 scans
Multiple conditions, time points, and metabolites can be given
The segmentation file must be in a format that is readable by 3DSlicer as a vtkMRMLSegmentationNode (by convention the file name ends with .seg.nrrd, but that is not required)
The outputs of this script are stored in the user's Documents folder under a folder named 'StatsCollector'

Note: This script assumes that the number of volumes (time points) for all metabolites are the same
"""


# This class converts all the DICOMs into Nrrd volume files
class NrrdConverterLogic(object):

	# Constructor for the DicomToNrrdConverter
	def __init__(self, pathToDicoms, pathToConverter, excludeDirs):
		# Parse paths and store them into instance variables
		self.pathToDicoms = os.path.normpath(pathToDicoms)
		self.converter = os.path.normpath(pathToConverter)
		# List of folder names to exclude
		self.excludeDirs = excludeDirs
		# If one of the paths does not exist, throw an error
		if not os.path.exists(self.pathToDicoms) or not os.path.exists(self.converter):
			raise IOError("DICOMs or DicomToNrrdConverter.exe does not exist")

	# Loop through directory given to find directories with .dcm files, return a list of those directory paths
	def getDicomDirs(self):
		# Get a list of 3-tuples, containing a recursive list of directories
		pathWalk = os.walk(self.pathToDicoms)
		# Initialize an empty list to store the paths of directories containing DICOMs
		dicomDirs = []
		# Store the path to the directory being analyzed in 'root', a list of the directories in it in 'dirs', and a list of the files in it in 'files'
		for root, dirs, files in pathWalk:
			# Get just the folder name from the full path
			foldername = os.path.split(root)[1]
			# Only consider folder names that are not supposed to be excluded
			if foldername not in self.excludeDirs:
				# Iterate through all the files in 'root'
				for file in files:
					# If a file has an extension .dcm or .ima, consider its parent a DICOM directory
					if file.lower().endswith(".dcm") or file.lower().endswith(".ima"):
						# Store the full path to the DICOM directory
						dicomDirs.append(root)
		# Remove duplicates by converting list to a set because sets cannot contain any duplicates, then convert that set back into a list
		noDuplicates = list(set(dicomDirs))
		# Sort the list alphabetically in ascending order
		noDuplicates.sort()
		# Return the list of full DICOM directory paths
		return noDuplicates

	# Convert all DICOMs to Nrrd files with the names of their respective DICOM directories
	def convertToNrrd(self):
		# Get all DICOM directory paths as a list
		dicomDirs = self.getDicomDirs()
		# Initialize a dictionary to keep track of which DICOMs correspond to which condition, metabolite, and time point
		dcmDictionary = {}
		# Initialize a list to store the folder names in which the condition directories reside, to assess correct folder structure
		parentPaths = []
		for dicomDir in dicomDirs:
			# Set the volume name as the name of the DICOM directory (e.g. 8001)
			volName = os.path.split(dicomDir)[1]
			# Get the full path of the metabolite folder and its parent. The metabolite folder is the parent of the volume folder.
			metaboliteDirPath = os.path.split(os.path.split(dicomDir)[0])
			# Get the metabolite folder name from the full path (e.g. if C:/Data/Subj101/20percentOxygen/PyBy6/8001/x.dcm then this is PyBy6)
			metaboliteDirName = metaboliteDirPath[1]
			# Get the path of the condition, which is the parent of the metabolite (e.g. C:\Data\Subj101\100percentOxygen)
			conditionPaths = os.path.split(metaboliteDirPath[0])
			# Get the path of where the condition folder resides to assess correct folder structure
			parentPath = conditionPaths[0]
			# Get just the condition folder's name (e.g. 100percentOxygen)
			conditionDir = conditionPaths[1]
			# Specify an output directory path to hold Nrrd files in the user's 'Documents'
			documentsDir = os.path.normpath(os.path.expanduser(r"~\\Documents\\StatsCollector\\NrrdOutput"))
			# Check if the output path does not exist
			if not os.path.exists(documentsDir):
				# Recursively make all the directories of that path
				os.makedirs(documentsDir)
			# Specify the output file path for the temporary Nrrd file containing the volume in 'dicomDir'
			outputFilePath = os.path.normpath(documentsDir + "\\" + conditionDir + "-" + metaboliteDirName + "_" + volName + ".nrrd")
			# This is a workaround to Slicer's Python environment containing a different version of ITK library which is incompatible with DicomToNrrdConverter.exe
			runnerPath = os.path.split(self.converter)[0] + '\\runner.bat'
			# Specify the string to execute in the operating system's shell (e.g. Command Prompt for Windows or Bash for UNIX)
			execString = runnerPath + " " + self.converter + " --inputDicomDirectory " + dicomDir + " --outputVolume " + outputFilePath
			# Use DicomToNrrdConverter.exe to convert all DICOMs to a Nrrd file and supress stdout of converter
			os.system(execString + " > nul")

			# If the dictionary does not contain data for the current volume's condition, create it
			if not dcmDictionary.has_key(conditionDir):
				# Initialize an internal dictionary that contains a list of metabolites as the value, specified by the condition folder name as the key
				dcmDictionary[conditionDir] = {}
			
			# If the internal dictionary does not have data for the current volume's metabolite, create it
			if not dcmDictionary[conditionDir].has_key(metaboliteDirName):
				# Initialize a list to contain all the Nrrd file names corresponding to this condition and metabolite
				dcmDictionary[conditionDir][metaboliteDirName] = []

			# Store Nrrd file name to the metabolite's data list
			dcmDictionary[conditionDir][metaboliteDirName].append(outputFilePath)
			
			# Inform the user that the DICOMs were successfully converted
			logging.info("Successfully converted DICOMs in " + dicomDir)

			# Append the condition's parent folder to the list
			parentPaths.append(parentPath)

		# Remove duplicates from parentPath list
		parentPaths = list(set(parentPaths))
		# Check if the conditions live in different places
		if len(parentPaths) > 1:
			message = "The condition directories live in different folders, they must all be in the same folder...\nFound folders that contain possible conditions:" + str(parentPaths)
			message += "\nConsider using the '--excludedirs' argument to exclude specific Dicom-containing folders"
			raise IOError(message)

		# Return the whole dictionary which contains data for all conditions and metabolites
		return dcmDictionary

# This class gets the statistics from a Nrrd volume file, using a Nrrd segmentation file
class StatsCollectorLogic(object):
	# Constructor
	def __init__(self, segmentationFile, noiseSegment):
		# Store the path of the Nrrd segmentation file
		self.segFile = os.path.normpath(segmentationFile)
		# Get segmentation node from the file using Slicer3D's API
		self.segNode = slicer.util.loadSegmentation(self.segFile,returnNode=True)[1]
		# Dictionary to store file names and Openpyxl Workbook objects
		self.xlWorkbooks = {}
		# Store noise segment's name
		self.noiseSegment = noiseSegment
		# Dictionary to store all the stats of the segmentation from each volume
		self.metaStats = {}
		# Check whether --getsnr argument was specified
		self.getsnr = len(self.noiseSegment) != 0
		# If the argument was specified, get the noise segment ID for easy retrieval
		if self.getsnr:
			seg = self.segNode.GetSegmentation()
			for i in range(seg.GetNumberOfSegments()):
				if seg.GetNthSegment(i).GetName() == self.noiseSegment:
					self.noiseSegmentID = seg.GetNthSegmentID(i)

	# Function to parse a string into a float. If not, return the string back
	@staticmethod
	def digitize(s):
		# Try to convert the string into a float
		try:
			return float(s)
		# If that throws an Exception, return the string back instead
		except ValueError:
			return s

	# Function to compute the SNRs using the background's standard deviation and the segmentation's mean signal
	def computeSnrs(self, segStatLogic, segmentIDs, noiseStdev):
		for segmentID in segmentIDs:
			segStatLogic.statistics[segmentID, "SNR"] = segStatLogic.statistics[segmentID, "GS mean"] / noiseStdev
		return segStatLogic

	# Gets the specified sheet from the specified workbook
	def getWorkSheet(self, workbook, sheetName):
		# Get all the sheet names from the specified workbook
		existingSheetNames = workbook.get_sheet_names()
		# Parse the sheet names into readable strings
		existingSheetNames = [x.encode('UTF8') for x in existingSheetNames]

		# If the sheet exists in the workbook, return it
		if sheetName in existingSheetNames:
			return workbook.get_sheet_by_name(sheetName)
		# If the sheet does not exist in the workbook, return a newly created one
		else:
			return workbook.create_sheet(sheetName)

	# Make worksheets for raw signal, SNR, and SNR ratio relative to a specific denominator (e.g. by deafult, it is pyruvate as specified in the MetaExporter class below)
	def advancedData(self, denominatorMetabolite):
		# Get the segmentation from the segmentation node
		seg = self.segNode.GetSegmentation()
		# Get all the segment names in the segmentation
		segNames = [seg.GetNthSegment(segIndex).GetName() for segIndex in range(seg.GetNumberOfSegments())]
		# Remove the noise segment because we already retrieved its standard deviations
		segNames.remove(self.noiseSegment)
		# Iterate through each workbook
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
	def __init__(self, pathToDicoms, pathToConverter, segmentationFile, folderSaveName, keepNrrdDir, 
		noiseSegment, denominatorMetabolite, excludeDirs, hideRawSheets):
		self.converter = NrrdConverterLogic(pathToDicoms, pathToConverter, excludeDirs)
		self.sc = StatsCollectorLogic(segmentationFile, noiseSegment)
		self.folderSaveName = folderSaveName
		self.excludeDirs = excludeDirs
		if len(denominatorMetabolite) == 0:
			self.denominatorMetabolite = "01_pyrBy6"
		else:
			self.denominatorMetabolite = denominatorMetabolite

		# Get all volume names
		dcmDictionary = self.converter.convertToNrrd()
		
		for condition, conditionDict in dcmDictionary.items():
			if not condition in self.sc.metaStats:
				self.sc.metaStats[condition] = {}
			for metabolite, volumes in conditionDict.items():
				# Get stats for each volume
				for volume in volumes:
					saveName = os.path.join(self.folderSaveName, condition)
					self.sc.getStatForVol(volume, self.folderSaveName, condition, metabolite)

		# Parse the stats into a more readable table format
		self.sc.advancedData(self.denominatorMetabolite)
		# Export stats to XLSX files
		for wbName, wb in self.sc.xlWorkbooks.items():
			wb.remove_sheet(wb.worksheets[0])
			if hideRawSheets:
				worksheets = wb.get_sheet_names()
				keepnames = ["Raw Signal", "SNR", "Ratios"]
				for wsname in worksheets:
					if wsname not in keepnames:
						ws = wb.get_sheet_by_name(wsname)
						ws.sheet_state = 'hidden'
			try:
				wb.save(wbName)
			except IOError as e:
				print str(e)
				e.strerror += '\nPerhaps the file is open or used by another application'
				raise e

		# Delete the NrrdOutput directory by default
		if not keepNrrdDir:
			shutil.rmtree(os.path.normpath(os.path.expanduser(r"~\\Documents\\StatsCollector\\NrrdOutput")))
