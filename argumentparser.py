import vtkSegmentationCorePython as vtkSegmentationCore
import vtkSlicerSegmentationsModuleLogicPython as vtkSlicerSegmentationsModuleLogic
import os, slicer

class ArgumentError(ValueError):
	pass

# Argument dictionary
class ArgumentParser(object):
	# Parse arguments provided by the user to a dictionary Dict[Arg, [Values]]
	def ParseArgs(self, sysArgs):
		args = {}
		currentArg = ""
		for arg in sysArgs[1:]:
			if arg.startswith('--'):
				arg = arg.lower().lstrip('--')
				if arg not in args:
					currentArg = arg
					args[currentArg] = []
				else:
					raise ArgumentError("Argument " + arg + " already specified")
			else:
				if len(currentArg) == 0:
					raise ArgumentError("Arguments must start with '--'")
				else:
					args[currentArg].append(arg)

		return args

	def __init__(self, sysArgs):
		# ArgDict[ArgName, [ArgType, Optional]]
		self.argDict = {
		"pathtodicoms":[["path"],False],
		"segmentationfile":[["path"], False],
		"foldersavename":[["name"], False],
		"keepnrrddir":[["boolean"], True],
		"getsnr":[["segmentName"], True],
		"denominatormetabolite":[["name", "dcmFolder"], True],
		"excludedirs":[["name"], True],
		"hiderawsheets":[["boolean"], True]
		}
		self.args = self.ParseArgs(sysArgs)

	def ValidateArg(self, arg, argValues):
		# If the argument provided does not match a key in the arguments dictionary, it is invalid
		if arg.lower() not in self.argDict:
			raise ArgumentError("Unknown argument: " + arg.lower())
			return False
		argTypes = self.argDict[arg][0]
		for argType in argTypes:
			if argType != "boolean" and len(argValues) == 0:
				raise ArgumentError("Missing parameter for argument: " + arg)
				return False
			if argType == "path":
				if not os.path.exists(argValues[0]):
					raise ArgumentError("File/folder not found: " + argValues[0])
					return False
			elif argType == "name":
				if len(argValues[0]) == 0:
					raise ArgumentError("No parameters provided for argument: " + arg)
					return False
			elif argType == "boolean":
				# Normally, booleans do not have parameters (if the argument is given, it is automatically true. If it is not given, it is false by default)
				if not len(argValues) == 0:
					raise ArgumentError("No parameters are expected for boolean argument: " + arg)
					return False
			elif argType == "segmentName":
				segFile = self.args["segmentationfile"][0]
				segNode = slicer.util.loadSegmentation(segFile, returnNode=True)[1]
				# If provided path is not a real segmentation file or can't be read by Slicer, it is invalid
				if segNode is None:
					raise ArgumentError("Path is not a real segmentation file or can't be read by Slicer: " + segFile)
					return False
				seg = segNode.GetSegmentation()
				segNames = [seg.GetNthSegment(segIndex).GetName() for segIndex in range(seg.GetNumberOfSegments())]

				# If provided segmentation name is not found in the segmentation file provided, it is invalid
				if argValues[0] not in segNames:
					raise ArgumentError("Segment '" + argValues[0] + "' was not found in segmentation at: " + segFile + '\nFound Segments: ' + str(segNames))
					return False
			elif argType == "dcmFolder":
				pathToDicoms = self.args["pathtodicoms"][0]
				folderName = argValues[0]
				pathWalk = os.walk(pathToDicoms)
				dicomDirs = []
				for root, dirs, files in pathWalk:
					for file in files:
						if file.lower().endswith(".dcm") or file.lower().endswith(".ima"):
							# Get the metabolite folder name (parent of the volume folder)
							parentPath = os.path.split(root)[0]
							parentFolder = os.path.split(parentPath)[1]
							dicomDirs.append(parentFolder)

				# Remove duplicates
				dicomDirs = list(set(dicomDirs))

				if folderName not in dicomDirs:
					raise ArgumentError("The specified folder does not contain any .dcm or .ima files: " + folderName + '\nFound directories: ' + str(dicomDirs))


	   # If all is satisfied, the argument is valid
		return True
	
	def ValidateAllArgs(self):
		# See if any non-optional arguments are missing
		for argName, argValues in self.argDict.items():
			# If the argument is not optional, see if it is missing
			if not argValues[1] and argName not in self.args:
				raise ArgumentError("Required argument " + argName + " was not specified")

		# Validate specific arguments by their type
		for arg, argValues in self.args.items():
			self.ValidateArg(arg, argValues)

		return True
	
	def GetArg(self, argName):
		# If the argument is a boolean, return whether it was provided or not
		if "boolean" in self.argDict[argName][0]:
			return argName in self.args
		# If the argument is other than a boolean
		else:
			# If it was provided, return its value
			if argName in self.args:
				return self.args[argName]
			# If it was not provided, return an empty string list
			else:
				return [""]

	def GetUsage(self, scriptName=""):
		usage = "\nUSAGE: " + scriptName + "\n"
		for argName, argFormat in self.argDict.items():
			usage += '--' + argName + ' ' + str(argFormat[0])
			if argFormat[1]:
				usage += ' (optional)'
			usage += '\n'
		return usage