# vManage-Template-Copy
This script will copy device templates from a source vManage to a target vManage.

Key points about the script:
----------------------------
- The scipt prompts the user for server and credential information.  It saves this information
  in the users local directory for future runs.
- It will parse the device template for all Feature Template dependancies and copy the
  neccessary Feature Templates to the target system.
- The script compares only template names to determine if a Device or Feature Template
  already exists on the target.  There is no guarantee that the templates are identical.
- It does not copy any Application Policy or Security Policy information at this time.  During
  the copy operation you have the choice to apply an existing Application Policy on the
  target system to the new device template.
- All Device and Feature templates will have " :: APIcopy" appended to the description so
  they can be easily identified on the target vManage.'''
