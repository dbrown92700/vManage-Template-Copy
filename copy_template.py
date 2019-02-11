#!/usr/bin/env python27
# -*- coding: utf-8 -*-
"""
Copyright (c) {{current_year}} Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.0 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

import json
import requests

__author__ = "David Brown <davibrow@cisco.com>"

##################################################################################
# Return the Org name by parsing the vSmart config
##################################################################################
def OrgName(server, admin, password):

	##################################################################################
	# Pull a list of devices. Find the vSmart uuid.
	##################################################################################

	URL = 'https://{0}/dataservice/device'.format(server)
	devices = requests.get(URL, auth=(admin,password), verify=False).text
	x = 0
	uuid = ''
	while uuid == '':
		if json.loads(devices)['data'][x]['device-type'] == 'vsmart':
			uuid = json.loads(devices)['data'][x]['uuid']
		x += 1

	##################################################################################
	# Pull the config and parse it for the Org name.
	##################################################################################

	URL = 'https://{0}/dataservice/template/config/attached/{1}'.format(server,uuid)
	config = requests.get(URL, auth=(admin,password), verify=False).text
	Ostart = config.find('organization-name') + 24
	Ofinish = config.find('\\n',Ostart)
	return config[Ostart:Ofinish].replace('\\','')

##################################################################################
# Return list of Device Templates as dictionary {templateId:templateName}
##################################################################################
def DevTempList(server, admin, password):
	URL = 'https://{0}/dataservice/template/device'.format(server)
	templates = requests.get(URL, auth=(admin,password), verify=False)
	template_list={}
	for entry in json.loads(templates.text)['data']:
		template_list.update({entry['templateId']:entry['templateName']})
	return template_list
	
##################################################################################
# Return list of Feature Templates as dictionary {templateId:templateName}
##################################################################################
def FeatTempList(server, admin, password):
	URL = 'https://{0}/dataservice/template/feature'.format(server)
	features = requests.get(URL, auth=(admin,password), verify=False).text
	template_list={}
	for entry in json.loads(features)['data']:
		template_list.update({entry['templateId']:entry['templateName']})
	return template_list

##################################################################################
# Return Device Template as a JSON Object
##################################################################################
def GetDevTemplate(server, admin, password, tid):
	URL = URL = 'https://{0}/dataservice/template/device/object/{1}'.format(server, tid)
	template = requests.get(URL, auth=(admin,password), verify=False).text
	return json.loads(template)

##################################################################################
# MAIN ROUTINE
##################################################################################
def main():

	##################################################################################
	# Get Org names from both systems..not needed for this operation
	##################################################################################
	
	#org1 = OrgName(server1, admin1, password1)
	#org2 = OrgName(server2, admin2, password2)

	##################################################################################
	# List templates from both systems
	##################################################################################
	
	DevTempList1 = DevTempList(server1, admin1, password1)
	DevTempList2 = DevTempList(server2, admin2, password2)

	##################################################################################
	# Get list of feature templates from both systems
	##################################################################################
	
	FeatTempList1 = FeatTempList(server1, admin1, password1)
	FeatTempList2 = FeatTempList(server2, admin2, password2)
	
	##################################################################################	
	# List out all Device Templates and prompt for template to copy
	##################################################################################
	print '\nCopy from {0} to {1}'.format(server1,server2)
	print '\nDEVICE TEMPLATES ON {0}'.format(server1)
	print '\nOption : Template Name                    Already On {0}'.format(server2)
	number = 0
	for entry in DevTempList1.values():
		print('{0:4}   : {1:40}'.format(number,entry)),
		if entry in DevTempList2.values():
			print ('YES')
		else:
			print ('no')
		number += 1
	copytemp = input('\nWhich template do you want to copy. Enter {} to quit: '.format(number))
	if copytemp == number:
		return False
	##################################################################################
	# Check if template exists
	##################################################################################
	
	if DevTempList1.values()[copytemp] in DevTempList2.values():
		print('\nERROR: That template name already exists in {}.'.format(server2))
		return True

	##################################################################################
	# If template doesn't exist
	##################################################################################
	
	else:

		# Pull the template definition
		templateID = DevTempList1.keys()[copytemp]
		URL = 'https://{0}/dataservice/template/device/object/{1}'.format(server1, templateID)
		DevTemp = json.loads(requests.get(URL, auth=(admin1,password1), verify=False).text)

		##################################################################################
		# Generate list of all feature templates in device template
		##################################################################################
		
		genTemplateList = []
		for entry in DevTemp['generalTemplates']:
			try:
				for sube in entry['subTemplates']:
					genTemplateList.append(sube['templateId'])
			except:
				True
			genTemplateList.append(entry['templateId'])
		
		##################################################################################
		# Check for each of the feature templates
		##################################################################################
		
		newTemplateList = {}
		for entry in genTemplateList:
			TempName = FeatTempList1[entry]
			
			##################################################################################
			# If the feature template exists add it's ID on org2 to the list
			##################################################################################
			
			if TempName in FeatTempList2.values():
				newTemplateList.update({entry:FeatTempList2.keys()[FeatTempList2.values().index(TempName)]})

			else:
				
				##################################################################################
				# If feature does not exist, copy Feature Template to New System and add ID to the list
				##################################################################################
				
				URL = 'https://{0}/dataservice/template/feature/object/{1}'.format(server1, entry)
				FeatTemp = json.loads(requests.get(URL, auth=(admin1,password1), verify=False).text)
				FeatTemp['templateDescription'] += ' :: APIcopy' 
				URL = 'https://{0}/dataservice/template/feature/'.format(server2)
				NewFeatUUID =  requests.post(URL, auth=(admin2,password2), verify = False,
					data = json.dumps(FeatTemp), headers = {'content-type': "application/json"})
				if NewFeatUUID.ok:
					newTemplateList.update({entry:json.loads(NewFeatUUID.text)['templateId']})
				else:
					print 'Copy failed for feature template {0}'.format(FeatTempList1[entry])
					print 'Error Output'
					print NewFeatUUID.text
		

		#DEBUG#for x in newTemplateList:
		#DEBUG#	print FeatTempList1[x] + ' - ' + x + ':' + newTemplateList[x]
		
		##################################################################################
		# Choose application policy to attach
		##################################################################################
		
		URL = 'https://{0}/dataservice/template/policy/vedge'.format(server2)
		Policies = json.loads(requests.get(URL, auth=(admin2,password2), verify=False).text)
		PolicyIDs = []
		print '\nApplication Policies defined on target system.\n0 : NONE'
		for entry in Policies['data']:
			PolicyIDs.append(entry['policyId'])
			print str(len(PolicyIDs)) + ' : ' + str(entry['policyName'])
		Policy = input('\nWhich policy do you want to attach to this configuration: ')

		#DEBUG# print 'ORIGINAL TEMPLATE\n' + json.dumps(DevTemp, indent=4)
		
		##################################################################################
		# Replace Application Policy and Remove Security Policy ... Not currently supported by this script
		##################################################################################
		
		if Policy == 0:
			DevTemp['policyId'] = ""
		else:
			DevTemp['policyId'] = PolicyIDs[Policy - 1]
		print '\nApplication Policy has been replaced by the one that already exists on the target system'
		try:
			policyID = DevTemp.pop('securityPolicyId')
			print '\nSecurity policy has been removed from the template.'
			print 'This script does not currently support copying the policy.\n'
		except:
			print 'No Security Policy Currently Attached'

		##################################################################################
		# Change Name and Remove Invalid Entries
		##################################################################################

		DevTemp.pop('templateId')		
		DevTemp['templateDescription'] += ' :: APIcopy'
		
		##################################################################################
		# Replace the feature template source UUID's in the Device Template with the target UUIDs
		##################################################################################
		
		DevTempS = json.dumps(DevTemp, indent=4)
		for UUID in newTemplateList:
			DevTempS = DevTempS.replace(str(UUID), str(newTemplateList[UUID]))		
		
		#DEBUG#print '\nNEW TEMPLATE\n' + DevTempS
		
		##################################################################################
		# Copy to New System
		##################################################################################
		
		URL = 'https://{0}/dataservice/template/device/feature/'.format(server2)
		NewDevID =  requests.post(URL, auth=(admin2,password2), verify = False,
			data = DevTempS, headers = {'content-type': "application/json"})
		if NewDevID.ok:
			print 'Device successfully copied to {0}'.format(DevTemp['templateName'])
		else:
			print 'Copy failed for device template {0}'.format(DevTemp['templateName'])
			print 'Error Output:'
			print NewDevID.text
		return True

##################################################################################
# RUN MAIN IF EXECUTED AS A SCRIPT
##################################################################################
if __name__ == "__main__":

	print '''
This script will copy device templates from a source vManage to a target vManage.
You can edit the variables at the beginning of the scipt to save your server information
permenantly.

Key points about the script:
----------------------------
- The scipt prompts the user for server and credential information. It saves this
  information in the users local directory for future runs.
- It will parse the device template for all Feature Template dependancies and copy the
  neccessary Feature Templates to the target system.
- The script compares only template names to determine if a Device or Feature Template
  already exists on the target.  There is no guarentee that the templates are identical.
- It does not copy any Application Policy or Security Policy information at this time.  During
  the copy operation you have the choice to apply an existing Application Policy on the
  target system to the new device template.
- All Device and Feature templates will have " :: APIcopy" appended to the description so
  they can be easily identified on the target vManage.'''

	##################################################################################
	# Get info for servers.  Info is saved as a file for future runs.
	##################################################################################

	try:
		passfile = open('server.txt','r')
		server1 = passfile.readline().rstrip('\n')
		admin1 = passfile.readline().rstrip('\n')
		password1 = passfile.readline().rstrip('\n')
		server2 = passfile.readline().rstrip('\n')
		admin2 = passfile.readline().rstrip('\n')
		password2 = passfile.readline().rstrip('\n')
		passfile.close()
	except:
		server1 = 'vmanage1.viptela.net'
		admin1 = 'admin'
		password1 = 'password'
		server2 = 'vmanage2.viptela.net'
		admin2 = 'admin'
		password2 = 'password'

	# Parameters for system to copy From
	print '\nEnter Source and Destination vManage information or hit return to take the displayed values'
	server1 = raw_input('Input source vManage [{}]: '.format(server1)) or server1
	admin1 = raw_input('Input source user [{}]: '.format(admin1)) or admin1
	password1 = raw_input('Input source password [{}]: '.format(password1)) or password1
	
	# Parameters for system to copy TO
	server2 = raw_input('Input destination vManage [{}] '.format(server2)) or server2
	admin2 = raw_input('Input destination user [{}]: '.format(admin2)) or admin2
	password2 = raw_input('Input destination password [{}]: '.format(password2)) or password2

	passfile = open('server.txt','w')
	for Line in [server1, admin1, password1, server2, admin2, password2]:
		passfile.write(Line + '\n')

	while main():
		True

	