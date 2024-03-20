
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from subprocess import run, PIPE
import argparse
import dxpy
import json
import os
import smtplib
import subprocess
import sys
import time

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
	parser.add_argument("-v","--version", action='version', version='%(prog)s version: March 2024')
	parser.add_argument('-e','--send_emails', help="Add email sender. Works when a download occures. (default=None)", default=None)

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

def send_individual_email(fromAddress, recipient, mySubject, body_of_email):
	return_value =  True
	try:
		msg = MIMEMultipart()
		msg['From'] = fromAddress
		msg['To'] = recipient
		msg['Subject'] = mySubject

		# mime_txt = MIMEText(unicode(core_member_msg), 'plain')
		mime_txt = MIMEText(body_of_email.as_string(), 'plain')
		msg.attach(mime_txt)
		text = msg.as_string()
		s = smtplib.SMTP('localhost')
		s.sendmail(fromAddress, recipient, text)
		username = recipient.split('@')
		username = username[0]
		s.quit()
		print ('\tSent to recipient: ' + recipient)
	except:
		print("\tERROR Failed to sent to: " + recipient)
		pass
		return_value =  False
	return return_value


def send_emails (proj_name, download_path, sendEmail, email_file_on_dnanexus):
	# https://docs.python.org/3/library/smtplib.html
	toAddress = None
	fromAddress = sendEmail.rstrip('\n')
	body_of_email = ""

	# print("\tEmail send from: " + fromAddress)
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
				toAddress.append(sendEmail)
			elif idx == 1: # then this is Email To: yyy@gmail.com
				mySubject = email_file_lines[1].replace("Subject: ","")
				mySubject = mySubject.rstrip("\n")
				print ("\tEmail subject: " + mySubject)
	body_of_email = MIMEText(body_of_email)

	## Send individual emails off
	failed_emails = []
	for recipient in toAddress:
		wasSent = send_individual_email(fromAddress, recipient, mySubject, body_of_email)
		if wasSent == False: failed_emails.append(recipient)
	failed_count = len(failed_emails)

	if failed_count > 0:
		body_of_email = "The following emailing occured for the following email addresses: \n\t" + str(failed_emails)
		send_individual_email(fromAddress, fromAddress, "ERROR with emailing: " + mySubject, MIMEText(body_of_email))

	mv_email_on_dnanexus_to_sent (email_file_on_dnanexus)

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
			if args.send_emails is not None: send_emails(proj_name, download_path, args.send_emails, email_file_on_dnanexus)

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
