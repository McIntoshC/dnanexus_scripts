
import os
from subprocess import run, PIPE
import subprocess
import time
import dxpy
import argparse
import json
import sys

## Global Variable
prog_name = "get_dnanexus_files_with_name.py"


## Get program arguments
# https://docs.python.org/3/library/argparse.html
def get_args():
	"""*get_args* - parses program's arg values.

	.. todo:: Task 2

	Returns
	arguments (*dict*) - user selected arguments parser.parse_args()

	"""
	parser = argparse.ArgumentParser(
		prog=prog_name,
		description='Description: Download all files of a given file name. ',
		epilog="Developed by Genome Analysis Unit: McIntosh, Carl.")

	#### Optional Parameters
	parser.add_argument("-v","--version", action='version', version='%(prog)s version: July 2021')

	#### Required
	group_req = parser.add_argument_group('required arguments')
	group_req.add_argument("-n","--file_name"        , help="Absolute File Name. " , required=True)

	#### Limit Downloads
	group_limit_files = parser.add_argument_group('limit downloads')
	group_limit_files.add_argument('--no_downloads', help="List files without downloading.", action='store_true')
	group_limit_files.add_argument('--use_blacklist', help="Use file with list of file-ids to exclude from downloading.", required=False)

	#### Limit Projects
	group_limit_projs = parser.add_argument_group('limit projects')
	group_limit_projs.add_argument("-p","--project_name", help="DNAnexus Project Name. ", required=True)

	return parser.parse_args()

def project_name(project_id):
	procs = subprocess.run(["dx", "describe", project_id, "--json"], stdout=PIPE)
	project_info = procs.stdout.decode("utf-8")
	project_info = json.loads(project_info)
	return project_info['name']

def append_blacklist(blacklist, file_id):
	with open(blacklist,'a') as FILE:
		FILE.writelines([file_id + '\n'])


######## main - start ##############################################################################
def main():
	"""*main* - main function.

	"""
	blacklist = None

	######## Parse arguments ########
	args = get_args()
	print("################################################################################")
	print("Program Name:         " + prog_name)
	print("Searching in Project: " + args.project_name)
	print("Searching for File  : " + args.file_name)
	print("################################################################################")
	procs = subprocess.run(["dx", "find", "data", "--name",  args.file_name, "--json","--path", args.project_name + ":/"], stdout=PIPE)
	files_json = procs.stdout.decode("utf-8")
	files_array = json.loads(files_json)
	file_count = len(files_array)
	print("INFO: Program found: " + str(file_count) + " files with name '" + args.file_name + ".'")
	print("--------------------------------------------------------------------------------")


	if (args.use_blacklist):
		print ("Loading blacklist : \n\t" + args.use_blacklist)

		try:
			with open(args.use_blacklist, 'r') as FILE:
				blacklist = FILE.read().split("\n")
				blacklist.remove("")
				blacklist_count=len(blacklist)
				print("\tBlacklist contains file count " + str(blacklist_count)+ "\n")
				print("--------------------------------------------------------------------------------")

		except:
			print("\tERROR: File could not be found: \n\t\t" + args.use_blacklist)
			print("\tCheck location of file and try again. Program will exit now.")
			sys.exit()

	for idx, str_dict in enumerate(files_array):
		file_dict = dict(files_array[idx])
		proj_name = project_name(file_dict["project"])
		isDownload = False
		isFoundInBlacklist = False

		if not args.no_downloads:
			# We are using a blacklist and it is in blacklist, then we will NOT download the file.
			if (args.use_blacklist and file_dict["id"] in blacklist):
				isDownload = False
				isFoundInBlacklist = True
			# We are using a blacklist AND it is not in blacklist, then we will download the file.
			elif (args.use_blacklist and file_dict["id"] not in blacklist):
				isDownload = True
				# add to backlist
				append_blacklist(args.use_blacklist, file_dict["id"])
				## Add to file

			# We are not using the a blacklist, so we will download the file.
			else:
				isDownload = True
		else:
			isDownload = False

		if isDownload:
			print("Downloading " + file_dict["id"] + " from location: ")
			print("\t" + proj_name + ":" + file_dict["describe"]["folder"] + "/\n")
			file_id_str = file_dict["id"].replace('-','_')
			subprocess.run(["dx", "download", "--no-progress", "--output", file_id_str + "_" + args.file_name, file_dict["id"]])

			blacklist.append(file_dict["id"])
		else:
			print("Not downloading " + file_dict["id"] + " from location: ")
			print("\t" + proj_name + ":" + file_dict["describe"]["folder"] + "/")
			if isFoundInBlacklist: print("\t## This File Found in Blacklist ##\n")

	print("--------------------------------------------------------------------------------")
	print("################################################################################")

if __name__ == "__main__":
	main()
######## main - end ################################################################################
