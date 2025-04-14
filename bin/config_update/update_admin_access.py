"""
Add or remove admin email addresses from admin_dashboard.admin_access
"""

import sys
import argparse
import re

from _util import read_config, update_config


def add_admin_email(config, email):
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$', email):
        print(f"{email} is an invalid email format - no changes made.")
        sys.exit(1)
    
    if email not in config.get('admin_dashboard', {}).get('admin_access', []):
        if 'admin_dashboard' not in config:
            config['admin_dashboard'] = {}
        if 'admin_access' not in config['admin_dashboard']:
            config['admin_dashboard']['admin_access'] = []
        config['admin_dashboard']['admin_access'].append(email)
        print(f"Added {email} to the admin_access list.")
    else:
        print(f"{email} is already an admin - no changes made.")
        return

    return config


def remove_admin_email(config, email):
    if email in config.get('admin_dashboard', {}).get('admin_access', []):
        config['admin_dashboard']['admin_access'].remove(email)
    else:
        print(f"{email} is not an admin - no changes made.")
        return

    return config


def update_admin_access(config, action, email):
    new_config = None
    if action == 'add':
        new_config = add_admin_email(config, email)
    elif action == 'remove':
        new_config = remove_admin_email(config, email)

    return new_config


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('deployment', type=str)
    parser.add_argument('action', type=str, help='Action to perform (add/remove)')
    parser.add_argument('email', type=str, help='Email address to add/remove')
    args = parser.parse_args()

    config = read_config(args.deployment)
    new_config = update_admin_access(config, args.action, args.email)
    if new_config:
        msg = f"update admin_access\n\n - {args.action} {args.email}"
        update_config(args.deployment, new_config, msg)
    else:
        print("No changes made.")
