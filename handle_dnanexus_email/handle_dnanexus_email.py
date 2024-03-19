
import os
from subprocess import run, PIPE
import subprocess
import time
import dxpy
import argparse
import json
import sys

## Global Variable
prog_name = "handle_dnanexus_email.py"


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
	parser.add_argument("-v","--version", action='version', version='%(prog)s version: July 2024')

	#### Required
	group_req = parser.add_argument_group('required arguments')
	group_req.add_argument('-o','--output', help=" Local filename or directory to be used; if not supplied or a directory is given, the object's name on the platform will be used, along with any applicable extensions.", default="./", required=False)

	#### Limit Downloads
	group_limit_files = parser.add_argument_group('limit downloads')
	group_limit_files.add_argument('--no_downloads', help="List files without downloading.", action='store_true')
	group_limit_files.add_argument('--use_exclude_file', help="Use file with list of file-ids to exclude from downloading.", required=False)

	#### Limit Projects
	group_limit_projs = parser.add_argument_group('limit projects')
	group_limit_projs.add_argument("-p","--project_name", help="DNAnexus Project Name. ", required=True)

	return parser.parse_args()

def project_name(project_id):
	procs = subprocess.run(["dx", "describe", project_id, "--json"], stdout=PIPE)
	project_info = procs.stdout.decode("utf-8")
	project_info = json.loads(project_info)
	return project_info['name']

def append_exclude_list(excludelist, file_id):
	with open(excludelist,'a') as FILE:
		FILE.writelines([file_id + '\n'])


######## main - start ##############################################################################
def main():
	"""*main* - main function.

	"""
	excludelist = None
	added_file_ids = []

	######## Parse arguments ########
	args = get_args()
	print("################################################################################")
	print("Program Name:         " + prog_name)
	print("Searching in Project: " + args.project_name)
	print("Download Directory:   " + args.output)
	print("################################################################################")
	procs = subprocess.run(["dx", "find", "data", "--json","--path", args.project_name + ":/email/pending"], stdout=PIPE)
	files_json = procs.stdout.decode("utf-8")
	files_array = json.loads(files_json)
	file_count = len(files_array)
	print("INFO: Program found: " + str(file_count) + " emails to be sent.")
	print("--------------------------------------------------------------------------------")

	if (args.use_exclude_file):
		print ("Loading excludelist : \n\t" + args.use_exclude_file)

		try:
			with open(args.use_exclude_file, 'r') as FILE:
				excludelist = FILE.read().split("\n")
				excludelist.remove("")
				excludelist_count=len(excludelist)
				print("\tExcludelist contains file count " + str(excludelist_count)+ "\n")
				print("--------------------------------------------------------------------------------")

		except:
			print("\tERROR: File could not be found: \n\t\t" + args.use_exclude_file)
			print("\tCheck location of file and try again. Program will exit now.")
			sys.exit()

	for idx, str_dict in enumerate(files_array):
		file_dict = dict(files_array[idx])
		proj_name = project_name(file_dict["project"])
		isDownload = False
		isFoundInExcludelist = False
		file_name = file_dict["describe"]["name"]

		if not args.no_downloads:
			# We are using a excludelist and it is in excludelist, then we will NOT download the file.
			if (args.use_exclude_file and file_dict["id"] in excludelist):
				isDownload = False
				isFoundInExcludelist = True
			# We are using a excludelist AND it is not in excludelist, then we will download the file.
			elif (args.use_exclude_file and file_dict["id"] not in excludelist):
				isDownload = True
				# add to backlist
				append_exclude_list(args.use_exclude_file, file_dict["id"])
				## Add to file

			# We are not using the a excludelist, so we will download the file.
			else:
				isDownload = True
		else:
			isDownload = False

		if isDownload:
			download_path = args.output + '/' + file_name
			download_path = download_path.replace('//','/')
			print("Downloading " + file_name + "(" + file_dict["id"] + ")")
			print("\tFrom Location: " + proj_name + ":" + file_dict["describe"]["folder"] + "/" + file_name)
			print("\tTo Location  : " + download_path)
			print("")

			subprocess.run(["dx", "download", "--no-progress", "--output", download_path ,file_dict["id"]])
			added_file_ids.append(file_dict["id"])
		else:
			print("Not downloading " + file_name + "(" + file_dict["id"] + ")")
			print("\tFrom Location: " + proj_name + ":" + file_dict["describe"]["folder"] + "/" + file_name)
			if isFoundInExcludelist: print("\t## This File Found in Exclude List ##\n")

	print("--------------------------------------------------------------------------------")
	print("Added file-ids:")
	print(added_file_ids)
	print("--------------------------------------------------------------------------------")
	print("################################################################################")

if __name__ == "__main__":
	main()
######## main - end ################################################################################
