# prints a comma-separated list of all email addresses found in the program configs

import os
import re

# get a list of all programs from the configs directory
programs = os.listdir('configs')

# or, specify programs manually:
# programs = [
#     'denver-casr.nrel-op.json',
#     'nrel-commute.nrel-op.json',
#     'open-access.nrel-op.json',
#     'ride2own.nrel-op.json',
#     'smart-commute-ebike.nrel-op.json',
#     # ...
# ]

print('Checking %d programs for email addresses...\n' % len(programs))

emails = []
for program in programs:
    with open('configs/'+program, 'r') as f:
        emails_for_program = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', f.read())
        emails_for_program = [e.rstrip(' .,') for e in emails_for_program]
        print(program + ' has emails: ' + str(emails_for_program))
        emails.extend(emails_for_program)

emails = list(set([e.lower() for e in emails]))
print('\nIn total, found ' + str(len(emails)) + ' emails:')
print(', '.join(emails))
