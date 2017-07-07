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
				if arg not in args:
					currentArg = arg.lstrip('--').lower()
					args[currentArg] = []
				else:
					raise ArgumentError("Argument " + arg.lstrip('--') + " already specified", arg)
			else:
				if len(currentArg) == 0:
					raise ArgumentError("Arguments must start with '--'")
				else:
					args[currentArg].append(arg)

		return args

	def __init__(self, sysArgs):
		# ArgDict[ArgName, [ArgType, Optional]]
		self.argDict = {"pathtodicoms":[["path"],False], "segmentationfile":[["path"], False], "foldersavename":[["name"], False], "keepnrrddir":[["boolean"], True], "getsnr":[["segmentName"], True], "denominatormetabolite":[["name"], True]}
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
					raise ArgumentError("File not found: " + argValues[0])
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
		# elif argType == "dcmFolder":
		# 	folderName = argValues[0]


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
		if argName in self.args:	
			if self.argDict[argName][0] == "boolean":
				return True
			return self.args[argName]
		else:
			# Return false by default if the missing argument is a boolean
			if self.argDict[argName][0] == "boolean":
				return False
			# If the argument was not provided, return an empty string list
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