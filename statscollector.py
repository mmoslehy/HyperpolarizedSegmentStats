import vtkSegmentationCorePython as vtkSegmentationCore
import vtkSlicerSegmentationsModuleLogicPython as vtkSlicerSegmentationsModuleLogic
import slicer, logging, os, shutil, subprocess
from SegmentStatistics import SegmentStatisticsLogic
import openpyxl

"""
By: Mohamed Moselhy (Western University), 2017
Uses 3DSlicer's SegmentStatistics module to extract data from hyperpolarized Carbon-13 scans
Multiple conditions, timepoints, and metabolites can be given
The segmentation file must be in a format that is readable by 3DSlicer as a vtkMRMLSegmentationNode (by convention the file name ends with .seg.nrrd, but that is not required)
The outputs of this script are stored in the user's Documents folder under a folder named 'StatsCollector'

Note: This script assumes that the number of volumes (timepoints) for all metabolites are the same
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
		# Initialize a dictionary to keep track of which volumes correspond to which condition and metabolite
		nrrdDictionary = {}
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
			# Specify the string to execute in the operating system's shell (e.g. Command Prompt for Windows or Bash for UNIX)
			execString = self.converter + " --inputDicomDirectory " + dicomDir + " --outputVolume " + outputFilePath
			# Use DicomToNrrdConverter.exe to convert all DICOMs to a Nrrd file and supress stdout of converter
			subprocess.call(execString + " > nul", shell=True, env={})

			# If the dictionary does not contain data for the current volume's condition, create it
			if not nrrdDictionary.has_key(conditionDir):
				# Initialize an internal dictionary that contains a list of metabolites as the value, specified by the condition folder name as the key
				nrrdDictionary[conditionDir] = {}
			
			# If the internal dictionary does not have data for the current volume's metabolite, create it
			if not nrrdDictionary[conditionDir].has_key(metaboliteDirName):
				# Initialize a list to contain all the Nrrd file names corresponding to this condition and metabolite
				nrrdDictionary[conditionDir][metaboliteDirName] = []

			# Store Nrrd file name to the metabolite's data list
			nrrdDictionary[conditionDir][metaboliteDirName].append(outputFilePath)
			
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
		return nrrdDictionary

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
		statistics = segStatLogic.getStatistics()
		segStatLogic.keys += ["SNR"]
		for segmentID in segmentIDs:
			statistics[(segmentID, "SNR")] = statistics[(segmentID, "ScalarVolumeSegmentStatisticsPlugin.mean")] / noiseStdev
		parNode = segStatLogic.getParameterNode()
		parNode.statistics = statistics
		segStatLogic.setParameterNode(parNode)
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

	# Make worksheets for raw signal
	def advancedRawData(self, denominatorMetabolite):
		# Get the segmentation from the segmentation node
		seg = self.segNode.GetSegmentation()
		# Get all the segment names in the segmentation
		segNames = [seg.GetNthSegment(segIndex).GetName() for segIndex in range(seg.GetNumberOfSegments())]
		# Iterate through each workbook and make a worksheet for Raw Signal
		for wbPath, wb in self.xlWorkbooks.items():
			# Get/create raw signal worksheet
			rawSignalWs = self.getWorkSheet(wb, "Raw Signal")
			# Get the condition using the output file name of the workbook
			condition = os.path.basename(wbPath).rstrip('.xlsx')
			# Iterate through each metabolite and make a table for it
			for seriesName, series in self.metaStats[condition].items():
				# Append row in worksheet with the series name
				rawSignalWs.append([seriesName])
				# Append row with indented segment names
				rawSignalWs.append([''] + segNames)

				# Iterate through each timepoint
				for i in range(len(series)):
					# Index for timepoint (starts at 1)
					rawRow = [i + 1]
					# Get all the statistics for this timepoint
					stats = series[i].statistics
					# Iterate through every segment
					for segmentID in stats["SegmentIDs"]:
						# Get the mean signal
						rawRow += [stats[(segmentID, "ScalarVolumeSegmentStatisticsPlugin.mean")]]
					# Append the all the segmentation's mean signals to a row
					rawSignalWs.append(rawRow)

	# Make worksheets for raw signal, SNR, and SNR ratio relative to a specific denominator (e.g. by deafult, it is pyruvate as specified in the MetaExporter class below)
	def advancedSnrData(self, denominatorMetabolite):
		# Get the segmentation from the segmentation node
		seg = self.segNode.GetSegmentation()
		# Get all the segment names in the segmentation
		segNames = [seg.GetNthSegment(segIndex).GetName() for segIndex in range(seg.GetNumberOfSegments())]
		# Remove the noise segment because we already retrieved its standard deviations
		segNames.remove(self.noiseSegment)
		# Iterate through each workbook and make worksheets for raw signal, SNR, and SNR ratios
		for wbPath, wb in self.xlWorkbooks.items():
			# Get/create worksheets
			rawSignalWs = self.getWorkSheet(wb, "Raw Signal")
			snrSignalWs = self.getWorkSheet(wb, "SNR")
			ratioWs = self.getWorkSheet(wb, "Ratios")
			# Get the condition using the output file name of the workbook
			condition = os.path.basename(wbPath).rstrip('.xlsx')
			# Get the statistics for the denominator metabolite
			denominatorMetaboliteSeries = self.metaStats[condition][denominatorMetabolite]
			# Iterate through each metabolite and make a table for it			
			for seriesName, series in self.metaStats[condition].items():
				# Add headers to the tables
				rawSignalWs.append([seriesName])
				rawSignalWs.append([''] + segNames + ['BG STDEV'])
				snrSignalWs.append([seriesName])
				snrSignalWs.append([''] + segNames)
				# If the current series name is not the same as the denominator metabolite, then we should get the ratio for it
				if seriesName != denominatorMetabolite:
					ratioWs.append([seriesName])
					ratioWs.append([''] + segNames)
				# Iterate through each timepoint in the series
				for i in range(len(series)):
					# Index for timepoint (starts at 1)
					rawRow = [i + 1]
					snrRow = [i + 1]
					ratioRow = [i + 1]
					# Get all the statistics for this timepoint
					stats = series[i].getStatistics()
					# Iterate through every segment
					for segmentID in stats["SegmentIDs"]:
						# Get the mean signal and SNR if the segment is not the background
						if segmentID != self.noiseSegmentID:
							rawRow += [(stats[segmentID, "ScalarVolumeSegmentStatisticsPlugin.mean"])]
							snrRow += [stats[(segmentID, "SNR")]]
							# Get the ratio if the series name is not the same as the denominator metabolite
							if seriesName != denominatorMetabolite:
								ratioRow += [stats[(segmentID, "SNR")] / denominatorMetaboliteSeries[i].getStatistics()[(segmentID, "SNR")]]
					# Get the standard deviation of the noise segment in this timepoint
					rawRow += [stats[(self.noiseSegmentID, "ScalarVolumeSegmentStatisticsPlugin.stdev")]]
					# Append the worksheet with the rows
					rawSignalWs.append(rawRow)
					snrSignalWs.append(snrRow)
					if seriesName != denominatorMetabolite:
						ratioWs.append(ratioRow)

	# Get the specified Workbook object
	def getWorkBook(self, workbookName):
		if not self.xlWorkbooks.has_key(workbookName):
			# If it doesn't exist, instantiate an openpyxl Workbook object
			self.xlWorkbooks[workbookName] = openpyxl.Workbook()
		return self.xlWorkbooks[workbookName]

	# Parse the SegmentStatisticsLogic into a workbook
	def exportStatsToXl(self, segStatLogic, outputFileName, header="", sheetName=""):
		# If the output file name does not end with the xlsx extension (MS Excel 2007+ format), then add it
		if not outputFileName.lower().endswith('.xlsx'):
			outputFileName += '.xlsx'

		# Get the workbook object that this timepoint should be in
		wb = self.getWorkBook(outputFileName)

		# Get the raw statistics (as it would look like in the SegmentStatistics module when exported to table)
		stats = segStatLogic.exportToString()
		# Split the table by row
		rows = stats.split('\n')

		# Get the worksheet that was specified as a parameter
		ws = self.getWorkSheet(wb, sheetName)

		# Append the specified header to the worksheet
		ws.append([header])
		# Split the first row by comma, to get the column names (e.g. "mean")
		columnTitles = rows[0].split(',')
		# Make the titles more readable (Remove the Slicer prefixes)
		newTitles = []
		for x in columnTitles:
			if len(x.split('.')) > 1:
				newTitles.append(x.split('.')[1])
			else:
				newTitles.append(x)
		columnTitles = newTitles
		columnTitles = [x.rstrip("\"") for x in columnTitles]
		columnTitles = [x.lstrip("\"") for x in columnTitles]
		# Append the column titles to the worksheet
		ws.append(columnTitles)

		# Iterate through every row under the header (rows 1 and after)
		for row in rows[1:]:
			# Split the rows by comma to get the values
			items = row.split(',')
			# Parse each value into a float
			items[:] = [self.digitize(x) for x in items]
			# Add the values to the worksheet
			ws.append(items)

	# Get statistics for a specific volume/timepoint
	def getStatForVol(self, volFile, folderSaveName, condition, seriesName=""):
		# Load the volume, get a tuple of (success, vtkMRMLScalarVolumeNode)
		vol = slicer.util.loadVolume(volFile, returnNode=True)

		# If the volume was not successfully loaded, exit
		if not vol[0]:
			# Print error if volume does not exist or is inaccessible
			raise IOError("Volume could not be loaded from: " + volFile)

		# Get the volume node
		volNode = vol[1]

		# Instantiate a SegmentStatisticsLogic object to store the statistics
		segStatLogic = SegmentStatisticsLogic()
		segStatLogic.getParameterNode().SetParameter("Segmentation", self.segNode.GetID())
		segStatLogic.getParameterNode().SetParameter("ScalarVolume", volNode.GetID())
		# Compute the statistics using the specified volume as the master volume
		segStatLogic.computeStatistics()

		# If the --getsnr argument was specified
		if self.getsnr:
			statistics = segStatLogic.getStatistics()
			# Get the noise segment's standard deviation
			noiseStdev = statistics[(self.noiseSegmentID, "ScalarVolumeSegmentStatisticsPlugin.stdev")]
			# Compute the SNRs of other segments
			segStatLogic = self.computeSnrs(segStatLogic, statistics['SegmentIDs'], noiseStdev)

		# If this object's statistics dictionary does not contain this series
		if seriesName not in self.metaStats[condition]:
			# Initialize it into an empty list
			self.metaStats[condition][seriesName] = []

		# Append current volume's statistics to the statistics dictionary
		self.metaStats[condition][seriesName].append(segStatLogic)

		# Specify the folder name of output
		documentsDir = os.path.normpath(os.path.expanduser(r"~\\Documents\\StatsCollector\\SegmentStatistics"))
		# Specify the folder path of the output
		fileParentDir = os.path.join(documentsDir, folderSaveName)
		# Specify the full file path of the Excel file to output
		filePath = os.path.join(fileParentDir, condition)

		# Make the folder directories if they don't exist
		if not os.path.exists(fileParentDir):
			os.makedirs(fileParentDir)

		# Export the stats to a file
		self.exportStatsToXl(segStatLogic, filePath, volNode.GetName(), seriesName)

# When initialized, it uses all the methods above to create the statistics files
class MetaExporter(object):
	# Constructor to be called when object of this class is instantiated
	def __init__(self, pathToDicoms, pathToConverter, segmentationFile, folderSaveName, keepNrrdDir, 
		noiseSegment, denominatorMetabolite, excludeDirs, hideRawSheets, csv):
		# Instantiate NrrdConverterLogic and StatsCollectorLogic objects
		converter = NrrdConverterLogic(pathToDicoms, pathToConverter, excludeDirs)
		sc = StatsCollectorLogic(segmentationFile, noiseSegment)
		# If no denominator metabolite was specified as an argument, use pyruvate by default
		if len(denominatorMetabolite) == 0:
			denominatorMetabolite = "01_pyrBy6"

		# Get the dictionary containing all the Nrrd paths organized by condition and metabolite
		nrrdDictionary = converter.convertToNrrd()
		
		# Iterate through each condition in the dictionary
		for condition, conditionDict in nrrdDictionary.items():
			# If the statistics dictionary does not contain data for the condition, create it
			if not condition in sc.metaStats:
				sc.metaStats[condition] = {}
			# Iterate through each metabolite in the condition dictionary
			for metabolite, volumes in conditionDict.items():
				# Iterate through each volume in metabolite
				for volume in volumes:
					# Specify the file name
					saveName = os.path.join(folderSaveName, condition)
					# Get statistics for that volume
					sc.getStatForVol(volume, folderSaveName, condition, metabolite)

		# Parse the stats into a more readable table format
		if sc.getsnr:
			sc.advancedSnrData(denominatorMetabolite)
		else:
			sc.advancedRawData(denominatorMetabolite)

		# Iterate through each Workbook
		for wbName, wb in sc.xlWorkbooks.items():
			# By default, when a Workbook is instantiated, openpyxl creates an empty worksheet, delete that one
			wb.remove_sheet(wb.worksheets[0])
			# If the --hiderawsheets argument was specified
			if hideRawSheets:
				# Get a list of the sheet names in that workbook
				worksheets = wb.get_sheet_names()
				# Specify which sheet names to keep
				keepnames = ["Raw Signal", "SNR", "Ratios"]
				# Iterate through each worksheet in that Workbook
				for wsname in worksheets:
					# If the worksheet is not in the list that should be kept
					if wsname not in keepnames:
						# Get the worksheet object
						ws = wb.get_sheet_by_name(wsname)
						# Hide the worksheet
						ws.sheet_state = 'hidden'

			# If the user wants CSV files to be saved, extract each worksheet into a separate CSV file
			if csv:
				import csv
				for ws in wb.worksheets:
					csvdir = os.path.join(os.path.dirname(wbName), "CSV")
					if not os.path.exists(csvdir):
						os.makedirs(csvdir)
					csvname = "%s-%s.csv" % (os.path.basename(wbName).rstrip('.xlsx'), ws.title)
					csvpath = os.path.join(csvdir, csvname)

					with open(csvpath, 'wb') as file:
						writer = csv.writer(file)
						for row in ws.rows:
							writer.writerow([cell.value for cell in row])

			# Try saving the Workbook object into a file
			try:
				wb.save(wbName)
			# If an input/output error occurs, throw an Exception and give a suggestion
			except IOError as e:
				e.strerror += '\nPerhaps the file is open or used by another application'
				raise e

		# Delete the NrrdOutput directory by default, if the --keepnrrddir argument is not specified
		if not keepNrrdDir:
			shutil.rmtree(os.path.normpath(os.path.expanduser(r"~\\Documents\\StatsCollector\\NrrdOutput")))
