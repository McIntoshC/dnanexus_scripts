
import os
from subprocess import run, PIPE
import subprocess
import time
import dxpy
import argparse
import json
import sys
from smtplib import SMTP

## Global Variable
prog_name = "handle_dnanexus_email.py"

##

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
	parser.add_argument('-e','--send_emails', help="Email letters works when a download occures. (default=None)", default=None)

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

def create_email_file_stucture (proj_name):
	procs = subprocess.run(["dx", "mkdir", "--parents", proj_name + ":/email/pending"], stdout=PIPE)
	procs = subprocess.run(["dx", "mkdir", "--parents", proj_name + ":/email/sent"], stdout=PIPE)

def send_emails (proj_name, download_path, sendEmail):
	# https://docs.python.org/3/library/smtplib.html
	toAddress = None
	fromAddress = sendEmail.rstrip('\n')
	body_of_email = ""

	print("\tEmail send from: " + fromAddress)
	with open(download_path, 'r') as EMAIL_FILE:
		email_file_lines = EMAIL_FILE.readlines()
		for idx, str_dict in enumerate(email_file_lines):
			if idx > 1: # Then this is the body of the mail.
				body_of_email += email_file_lines[idx]
			elif idx == 0: # then this is Email To: yyy@gmail.com
				toAddress = email_file_lines[0].replace("Email To:","")
				toAddress = toAddress.replace(" ","")
				toAddress = toAddress.rstrip("\n")
				toAddress = toAddress.split(',')
				print("\tEmail send to  : " + str(toAddress))
			elif idx == 1: # then this is Email To: yyy@gmail.com
				mySubject = email_file_lines[1].replace("Subject: ","")
				mySubject = mySubject.rstrip("\n")
				print ("\tEmail subject: " + mySubject)

		# Modified from: https://docs.python.org/3/library/smtplib.html
		msg = ("From: %s\nTo: %s\nSubject: %s\n\n" % (fromAddress, ", ".join(toAddress) ,mySubject))
		msg = msg + body_of_email
		print("\tMessage length is", len(msg))

		print("\n\t################################################################################")
		print("\t" + msg.replace('\n','\n\t'))
		print("\t################################################################################")

		# server = smtplib.SMTP('localhost')
		# server.set_debuglevel(1)
		# server.sendmail(fromAddress, toAddress, msg)
		# server.quit()


def project_name(project_id):
	procs = subprocess.run(["dx", "describe", project_id, "--json"], stdout=PIPE)
	project_info = procs.stdout.decode("utf-8")
	project_info = json.loads(project_info)
	return project_info['name']

def append_exclude_list(excludelist, file_id):
	with open(excludelist,'a') as FILE:
		FILE.writelines([file_id + '\n'])

def mv_email_on_dnanexus_to_sent (source_email_file_on_dnanexus):
	print("\t## Moving letter to sent box. ##")
	dest_email_file_on_dnanexus = source_email_file_on_dnanexus.replace("/pending/", "/sent/")
	subprocess.run(["dx", "mv", source_email_file_on_dnanexus, dest_email_file_on_dnanexus])

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
	if args.send_emails is not None:
		print("Send emails:          " + str(args.send_emails))
	print("################################################################################")

	procs = subprocess.run(["dx", "find", "data", "--json","--path", args.project_name + ":/email/pending"], stdout=PIPE)
	files_json = procs.stdout.decode("utf-8")
	files_array = json.loads(files_json)
	file_count = len(files_array)
	print("INFO: Program found: " + str(file_count) + " emails to be send.")
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

		if idx < 1: create_email_file_stucture (proj_name)

		download_path = args.output + '/' + file_name
		download_path = download_path.replace('//','/')

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

		email_file_on_dnanexus = proj_name + ":" + file_dict["describe"]["folder"] + "/" + file_name
		if isDownload:
			print("Downloading " + file_name + "(" + file_dict["id"] + ")")
			print("\tFrom Location: " + email_file_on_dnanexus)
			print("\tTo Location  : " + download_path)
			print("")
			subprocess.run(["dx", "download", "--no-progress", "--output", download_path ,file_dict["id"]])
			added_file_ids.append(file_dict["id"])
			mv_email_on_dnanexus_to_sent (email_file_on_dnanexus)
			if args.send_emails is not None: send_emails(proj_name, download_path, args.send_emails)

		else:
			print("Not downloading " + file_name + "(" + file_dict["id"] + ")")
			print("\tFrom Location: " + email_file_on_dnanexus)
			if isFoundInExcludelist:
				print("\t## This File Found in Exclude List ##\n")
				mv_email_on_dnanexus_to_sent (email_file_on_dnanexus)


	print("--------------------------------------------------------------------------------")
	print("Added file-ids:")
	print(added_file_ids)
	print("--------------------------------------------------------------------------------")
	print("################################################################################")

if __name__ == "__main__":
	main()
######## main - end ################################################################################
