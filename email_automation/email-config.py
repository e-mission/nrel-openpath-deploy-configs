import boto3
from botocore.exceptions import ClientError
import json
import os
import logging
import sys
logger = logging.getLogger()
logger.setLevel(logging.INFO)

#Input the filename as an argument in command line 
filename_raw = sys.argv[1]
filename = filename_raw.split(".")[0]
pool_name = "nrelopenpath-prod-" + filename

current_path = os.path.dirname(__file__)
config_path = os.path.relpath('../configs/'+ filename_raw, current_path)

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
sts_client = boto3.client("sts")


def get_userpool_name(pool_name, cognito_client):
    response = cognito_client.list_user_pools(MaxResults=60)
    UserPoolExist = False
    #########One option to set the user pool without breaking (but still stop when condition met)
    i = 0
    while response["UserPools"][i]["Name"] != pool_name and i < len(response["UserPools"]) - 1:
        print("looking for user pool...")
        i = i + 1
        if response["UserPools"][i]["Name"] == pool_name:
            UserPoolExist = True
            pool_id = response["UserPools"][i]["Id"]
            print(pool_name + " pool exists! Checking for users...")
    #########Second option that uses a break when condition is met:
    # for i in response["UserPools"]:
    #     if i["Name"] == pool_name and not UserPoolExist:
    #         pool_id = i["Id"]
    #         UserPoolExist = True
    #         print(pool_name + " pool exists! Checking for users...")
    #         break 
    #     else:
    #         print("Looking for pool...")
    #         continue

    return UserPoolExist, pool_id

def user_already_exists(pool_id, email, cognito_client):
    try:
        response = cognito_client.list_users(UserPoolId=pool_id)
        users = response["Users"]
        result = False
        for i in users:
            for k, v in i.items():
                if k == "Attributes":
                    for j in v:
                        if j["Name"] == "email":
                            user_email = str(j["Value"])
                            if str(email) == user_email:
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
    account_num = sts_client.get_caller_identity()["Account"]
    identity_arn = "arn:aws:ses:" + AWS_REGION + ":" + account_num + ":identity/openpath@nrel.gov"
    return identity_arn

def email_extract():
    with open (config_path) as config_file:
        data = json.load(config_file)
        intro = data['intro']
        emails = [i.strip() for i in intro['admin_users'].split(",")]
        ####This section is in preparation for the next-level goal, which may involve customizing the email further based on the submission form.
        # admindash_prefs = data['admin_dashboard']
        # columns_exclude = admin_dash['data_trajectories_columns_exclude']
        # print("admindash", admindash_prefs)
    return emails

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
def format_email(pool_name):
    with open("welcome-template.txt", "r") as f:
        html = f.read()
        html = html.replace("<pool_name>", pool_name)
    return html

def update_user_pool(pool_id, pool_name, html, identity_arn, cognito_client):
  response = cognito_client.update_user_pool(
        UserPoolId= pool_id,
        AutoVerifiedAttributes=['email'],

        MfaConfiguration='ON',
        DeviceConfiguration={
            'ChallengeRequiredOnNewDevice': True,
            'DeviceOnlyRememberedOnUserPrompt': True
        },
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

UserPoolExist, pool_id = get_userpool_name(pool_name, cognito_client) 

 # Start by checking for the User Pool. If the User Pool does not yet exist, wait until it is set up to add users. 
if UserPoolExist:
    #extract email addresses from conf file
    emails = email_extract()
    #Loop over each email address. Check if they're in the user pool.
    for email in emails:
        if not user_already_exists(pool_id, email, cognito_client):   
            #If user not in pool, format the email template for their welcome email, update the user pool, and create an account for them.
            print(email + " not in user pool! Creating account...")
            html = format_email(pool_name)
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
  
