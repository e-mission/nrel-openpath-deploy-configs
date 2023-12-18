import boto3
from botocore.exceptions import ClientError
import json
import os
import logging
import sys
import argparse
logger = logging.getLogger()
logger.setLevel(logging.INFO)
# If you don't have boto3 installed, make sure to `pip install boto3` before running this script. 

#Input the filename as an argument in command line 
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-l', '--local',
                       help = 'Running locally. Provide full path to config file + install boto3 prior to running.' )
    group.add_argument('-g', '--github',
                       help = 'Must be run on GitHub. To run locally, use -l argument.') 
    args = parser.parse_args()
    filepath_raw = sys.argv[2]
    filename_raw = filepath_raw.split("/")[-1]
    filename = filename_raw.split('.')[0]
    pool_name = "nrelopenpath-prod-" + filename
    current_path = os.path.dirname(__file__)
    config_path = os.path.relpath('../configs/'+ filename_raw, current_path)

if args.local:
    #Set up AWS credentials as environment variables + set variables 
    ACCESS = os.environ.get("AWS_ACCESS_KEY_ID")
    SECRET = os.environ.get("AWS_SECRET_ACCESS_KEY")
    TOKEN = os.environ.get("AWS_SESSION_TOKEN")
    AWS_REGION = "us-west-2"

    #Set up clients
    cognito_client = boto3.client(
        'cognito-idp',
        aws_access_key_id = ACCESS,
        aws_secret_access_key= SECRET,
        aws_session_token=TOKEN, 
        region_name=AWS_REGION
        )

    sts_client = boto3.client(
        'sts',
        aws_access_key_id = ACCESS,
        aws_secret_access_key= SECRET,
        aws_session_token=TOKEN, 
        region_name=AWS_REGION
        )
# Functions 
def get_userpool_name(pool_name, cognito_client):
    response = cognito_client.list_user_pools(MaxResults=60)
    is_userpool_exist = False    
    user_pools = [user_pool["Name"] for user_pool in response["UserPools"]]
    is_userpool_exist = True if pool_name in user_pools else False
    user_pool_index = user_pools.index(pool_name) if is_userpool_exist else None
    pool_id = response["UserPools"][user_pool_index]["Id"]
    return is_userpool_exist, pool_id

def user_already_exists(pool_id, email, cognito_client):

    try:
        response = cognito_client.list_users(UserPoolId=pool_id)
        users = response["Users"]
        result = False
        if str(users).find(email) > 1:
            result = True
        return result
    except ClientError as err:
        logger.error(
            "Couldn't list users for %s. Here's why: %s: %s",
            pool_id,
            err.response["Error"]["Code"],
            err.response["Error"]["Message"],
        )
        raise

def get_verified_arn(sts_client):
    if args.local:
        account_num = sts_client.get_caller_identity()["Account"]
        identity_arn = "arn:aws:ses:" + AWS_REGION + ":" + account_num + ":identity/openpath@nrel.gov"
    if args.github:
        AWS_ACCT_ID = os.environ.get("AWS_ACCT_ID")
        identity_arn = "arn:aws:ses:" + AWS_REGION + ":" + AWS_ACCT_ID + ":identity/openpath@nrel.gov"
    return identity_arn

def email_extract():
    with open (config_path) as config_file:
        data = json.load(config_file)
        admindash_prefs = data['admin_dashboard']
        emails = [i.strip() for i in admindash_prefs['admin_access'].split(",")]
        columns_exclude = admindash_prefs['data_trips_columns_exclude']
        map_trip_lines_enabled = admindash_prefs['map_trip_lines']
    return emails, map_trip_lines_enabled, columns_exclude

def create_account(pool_id, email, cognito_client):
    response = cognito_client.admin_create_user(
                    UserPoolId = pool_id,
                    Username=email,
                    UserAttributes=[
                        {
                            'Name': 'email',
                            'Value': email,
                        },
                    ],
                    ForceAliasCreation=True,
                    DesiredDeliveryMediums=[
                        'EMAIL',
                    ],
                )
    return response

def format_email(filename, map_trip_lines_enabled, columns_exclude):
    with open('welcome-template.txt', 'r') as f:
        html = f.read()
        html = html.replace('<filename>', filename)
        if map_trip_lines_enabled:
            html = html.replace ('<map_trip_lines>', 'Additionally, you can view individual user-origin destination points using the "Map Lines" option from the map page.')
        else:
            html = html.replace ('<map_trip_lines>', '')
        if 'data.start_loc.coordinates' in columns_exclude or 'data.end_loc.coordinates' in columns_exclude:
            html = html.replace ('<columns_exclude>', 'Per your requested configuration, your trip table excludes trip start/end coordinates for greater anonymity. Let us know if you need them to be enabled for improved analysis.')
        elif columns_exclude == '':
            html = html.replace ('<columns_exclude>', 'Since you indicated that you want to map the data to infrastructure updates, your configuration includes trip start/end in the trip table. Let us know if you would like to exclude those for greater anonymity.')
        return html
        

def update_user_pool(pool_id, pool_name, html, identity_arn, cognito_client):
  response = cognito_client.update_user_pool(
        UserPoolId= pool_id,
        AutoVerifiedAttributes=['email'],
        EmailConfiguration={
            'SourceArn': identity_arn,
            'EmailSendingAccount': 'DEVELOPER',
            'From': 'openpath@nrel.gov'
        },
        AdminCreateUserConfig={
            'AllowAdminCreateUserOnly': True,
            'InviteMessageTemplate': {
                'EmailMessage': str(html),
                'EmailSubject': f'Welcome to {pool_name} user pool!'
            }
        },
)
######################################################################
is_userpool_exist, pool_id = get_userpool_name(pool_name, cognito_client) 

 # Start by checking for the User Pool. If the User Pool does not yet exist, wait until it is set up to add users. 
if is_userpool_exist:
    #extract email addresses from config file
    emails, map_trip_lines_enabled, columns_exclude = email_extract()
    #Loop over each email address. Check if they're in the user pool.
    for email in emails:
        if not user_already_exists(pool_id, email, cognito_client):   
            #If user not in pool, format the email template for their welcome email, update the user pool, and create an account for them.
            print(email + " not in user pool! Creating account...")
            html = format_email(filename, map_trip_lines_enabled, columns_exclude)
            identity_arn = get_verified_arn(sts_client)
            update_user_pool(pool_id, pool_name, html, identity_arn, cognito_client)
            response = create_account(pool_id, email, cognito_client)
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                print("Account created! Sending welcome email.")
            else:
                print("Account creation unsuccessful.")
                print(response['ResponseMetadata']['HTTPStatusCode'])       
        else:
            print(email + " already in user pool!")
else:
    print(pool_name + " does not exist! Try again later.")
  
