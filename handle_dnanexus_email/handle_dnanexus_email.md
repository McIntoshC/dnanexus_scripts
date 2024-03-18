# handle_dnanexus_email.py

## Algoritm Overview
This script will have the following actions:
1. For a given project, an Applet will compose an email of the form and location: ***\<DNAnexus Project\>:/email/\<Job-ID\>_notice.email.txt***
2. A ***Helix*** cron job periodically runs *handle_dnanexus_email.py* which will have the following actions:
	1. Download email files from ***\<DNAnexus Project\>:/email/\<Job-ID\>_notice.email.txt*** to ***Helix***.
	2. Move from ***\<DNAnexus Project\>:/email/\<Job-ID\>_notice.email.txt*** to ***\<DNAnexus Project\>:/sent_email/\<Job-ID\>_notice.email.txt***
	3. Email contents of ***\<Helix Sent Directory Location\>\\<Job-ID\>_notice.email.txt***
	4. Exit.

## Email Syntax
***\<Job-ID\>_notice.email.txt*** will have the following requirements:
```TEXT
Email To: thing1@gmail.com,thing2@gmail.com,thing3d@gmail.com
Subject: Some useful 1 line subject on line 2. >
Some useful email letter content of one or more lines.
```
