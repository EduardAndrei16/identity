import requests
import time
import json
import base64
import logging
import threading
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import instance, username, password, gitlab_token, project_id, okta_domain, api_token

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)

# Global variables
processed_tickets = set()


def check_okta_app_status(app_name):
    url = f"https://{okta_domain}/api/v1/apps"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'SSWS {api_token}'
    }
    
    all_apps = []
    while url:
        response = http.get(url, headers=headers)
        apps = response.json()
        all_apps.extend(apps)
        
        # Get next page URL from Link header
        url = None
        if 'Link' in response.headers:
            links = response.headers['Link'].split(',')
            for link in links:
                if 'rel="next"' in link:
                    url = link[link.find('<')+1:link.find('>')]
    
    # Search through all retrieved apps
    for app in all_apps:
        if isinstance(app, dict) and app.get('label') == app_name:
            return app
    return None
def get_saml_metadata(app_id):
   
    url = f"https://{okta_domain}/api/v1/apps/{app_id}/metadata.xml"
    headers = {
        'Accept': 'application/xml',
        'Authorization': f'SSWS {api_token}'
    }
    
    response = http.get(url, headers=headers)
    return response.text
def get_oidc_credentials(app_id):
    
    
    url = f"https://{okta_domain}/api/v1/apps/{app_id}/credentials/client"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'SSWS {api_token}'
    }
    
    response = http.get(url, headers=headers)
    return response.json()
def send_request_to_cody(ticket_id, 
                         app_name,
                         app_type,
                         app_owner_email,
                         saml_sign_on_url,
                         saml_entity_id,
                         passport_policies,
                         attribute_statements,
                         group_statements,
                         oidc_sign_in,
                         oidc_group_claims,
                         oidc_sign_out):
    url = "https://getcody.ai/api/v1/messages"
    headers = {
        "Authorization": "Bearer mQiou0zPaTmNwMQxioUOJfhEAJkstepjUbOkr8cU9240af34",
        "Content-Type": "application/json"
    }
    
    payload = {
        "content": f"""Create a {app_type} Okta Application with the name {app_name} in terraform language. If the app type is SAML use the following values:
  
  sso_url                  = {saml_sign_on_url}
  recipient                = {saml_sign_on_url}
  destination              = {saml_sign_on_url}
  audience                 = {saml_entity_id}
  subject_name_id_template should be $$user.userName
  subject_name_id_format   = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
  response_signed          = true
  signature_algorithm      = "RSA_SHA256"
  digest_algorithm         = "SHA256"
  honor_force_authn        = false
  authn_context_class_ref  = "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport"

        If the application type is OIDC, create an okta_app_oauth resource with the following values:
  type           = "web"
  grant_types    = ["authorization_code", "refresh_token"]
  redirect_uris  = {oidc_sign_in}
  response_types = ["code"]
post_logout_redirect_uri = {oidc_sign_out}
  And include {oidc_group_claims}  

        No matter what the application type is, take into consideration the following:

        Assign the application to the groups named {passport_policies} and create a data okta_group for each group and inside each data use the following syntax name = "the name of the group"
        Use a group assignment resource for each group assignement, if there are more than one groups, add the priority attribute to the resource, if the are more that 3 groups use a query instead if they start with the same name
        Please reply only with the application config.
        Organize this Terraform configuration into a clear structure
        The name of the resources and datas should include the name of the application in lowercase letters
        Do not use the preconfigured_app attribute and do not not use variables
        Include any data in the same file with the config and do not create any outputs
        Do not use a provider statement, org data and api key is already included into the repo and do not include any notes in the config, I want only the tf code.
       """,
        "conversation_id": "open5x7YYd7A"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response_text = response.text
    
    logger.info(f"\nCody's response for ticket {ticket_id}:\n{response_text}\n")
    
    with open(f'terraform_{ticket_id}.tf', 'w') as f:
        f.write(response_text)
    
    return response_text
def extract_terraform_code(convert_me_txt):
    try:
        response_data = json.loads(convert_me_txt)
        clean_hcl = response_data['data']['content']
        # Remove all backtick variants including single ones
        clean_hcl = clean_hcl.replace('', '').replace('``hcl', '').replace('`hcl', '')
        clean_hcl = clean_hcl.replace('', '').replace('``', '').replace('`', '').strip()
        clean_hcl = clean_hcl.replace('', '').replace('', '')
        clean_hcl = clean_hcl.encode().decode('unicode_escape')
        
        logger.info(f"Extracted Terraform code:\n{clean_hcl[:200]}...")
        
        with open('okta_saml_config.tf', 'w') as tf_file:
            tf_file.write(clean_hcl)
        
        return clean_hcl
    except json.JSONDecodeError:
        clean_hcl = convert_me_txt.strip()
        # Remove all backtick variants including single ones
        clean_hcl = clean_hcl.replace('', '').replace('``hcl', '').replace('`hcl', '')
        clean_hcl = clean_hcl.replace('', '').replace('``', '').replace('`', '').strip()
        
        logger.info(f"Using raw text as Terraform code:\n{clean_hcl[:200]}...")
        
        with open('okta_saml_config.tf', 'w') as tf_file:
            tf_file.write(clean_hcl)
            
        return clean_hcl
def commit_and_create_mr(file_content, gitlab_token, project_id, ticket_number):
    if not file_content or file_content.isspace():
        logger.info(f"File content is empty for ticket {ticket_number}")
        return False
        
    headers = {
        'PRIVATE-TOKEN': gitlab_token,
        'Content-Type': 'application/json'
    }
    
    source_branch = str(ticket_number) + '_saml_app_v8'
    target_branch = 'main'    
    
    # Create branch
    logger.info(f"Creating new branch: {source_branch}")
    branch_url = f'https://gitlab.booking.com/api/v4/projects/{project_id}/repository/branches'
    branch_data = {
        'branch': source_branch,
        'ref': target_branch
    }
    branch_response = requests.post(branch_url, headers=headers, json=branch_data)
    
    if branch_response.status_code not in [201, 200]:
        logger.error(f"Failed to create branch. Status: {branch_response.status_code}")
        logger.error(f"Response: {branch_response.text}")
        return False

    # Ensure content is properly formatted and encoded
    try:
        # Remove any BOM characters and normalize line endings
        cleaned_content = file_content.replace('\ufeff', '').replace('\r\n', '\n')
        content_encoded = base64.b64encode(cleaned_content.encode('utf-8')).decode('utf-8')
        
        commit_payload = {
            'branch': source_branch,
            'commit_message': f'Add Okta App configuration for ticket: {ticket_number}',
            'actions': [{
                'action': 'create',
                'file_path': f'okta_apps/{ticket_number}/okta_saml_config.tf',
                'content': content_encoded,
                'encoding': 'base64'
            }]
        }
        
        # Create commit
        logger.info(f"Creating commit in branch {source_branch}")
        commit_url = f'https://gitlab.booking.com/api/v4/projects/{project_id}/repository/commits'
        commit_response = requests.post(commit_url, headers=headers, json=commit_payload)
        
        if commit_response.status_code not in [201, 200]:
            logger.error(f"Failed to create commit. Status: {commit_response.status_code}")
            logger.error(f"Response: {commit_response.text}")
            return False
            
        # Create merge request
        logger.info(f"Creating merge request from {source_branch} to {target_branch}")
        mr_url = f'https://gitlab.booking.com/api/v4/projects/{project_id}/merge_requests'
        mr_payload = {
            'source_branch': source_branch,
            'target_branch': target_branch,
            'title': f'Add Okta SAML configuration for {ticket_number}',
            'description': 'Adding new Okta SAML configuration file, This is a TEST, do not approve the MR'
        }
        mr_response = requests.post(mr_url, headers=headers, json=mr_payload)
        
        if mr_response.status_code not in [201, 200]:
            logger.error(f"Failed to create merge request. Status: {mr_response.status_code}")
            logger.error(f"Response: {mr_response.text}")
            return False
            
        logger.info(f"Successfully created commit and merge request for ticket {ticket_number}")
        return True
        
    except Exception as e:
        logger.error(f"Error during commit process: {str(e)}")
        return False

def main(app_name,
        app_type,
        app_owner_email,
        saml_sign_on_url,
        saml_entity_id,
        passport_policies,
        attribute_statements,
        group_statements,
        oidc_sign_in,
        oidc_group_claims,
        oidc_sign_out):
                        
    # Use these values in your request to Cody
    ticket_id = app_owner_email  # Using app_owner_email as the ticket_id
    
    response = send_request_to_cody(
        ticket_id,
        app_name,
        app_type,
        app_owner_email,
        saml_sign_on_url,
        saml_entity_id,
        passport_policies,
        attribute_statements,
        group_statements,
        oidc_sign_in,
        oidc_group_claims,
        oidc_sign_out
    )
                        
    file_content = extract_terraform_code(response)
    success = commit_and_create_mr(file_content, gitlab_token, project_id, app_owner_email)

    if success:
        logger.info("File Commited to Git")                        
if __name__ == "__main__":
        try:
            main()
        except KeyboardInterrupt:
            logger.info("Script stopped by user")
        except Exception as e:
            logger.error(f"Critical error: {str(e)}")
            
