#!/usr/bin/env python
"""
Wrapper script to run the app_onboarding.py script with form data
"""
import sys
import json
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'identity_project.settings')

# Import Django and set it up
import django
django.setup()

def process_form_data(form_data, user_id):
    """
    Process the form data, save to database, and call the main function from app_onboarding.py
    """
    # Import Django-related modules inside the function to avoid setup issues
    from django.contrib.auth.models import User
    from main.models import Application
    from main.scripts.app_onboarding import main
    
    try:
        # Get the user
        user = User.objects.get(id=user_id)
        logger.info(f"Processing application submission for user: {user.username}")
        
        app_type = form_data.get('app_type')
        app_name = form_data.get('app_name', 'New Application')
        
        # Initialize parameters
        saml_sign_on_url = ''
        saml_entity_id = ''
        passport_policies = ''
        attribute_statements = []
        group_statements = []
        oidc_sign_in = []
        oidc_group_claims = []
        oidc_sign_out = []
        
        # Create a new Application object
        application = Application(
            name=app_name,
            app_type=app_type,
            owner=user,
            status='pending'
        )
        
        # Process SAML specific parameters
        if app_type == 'SAML':
            saml_sign_on_url = form_data.get('saml_sso_url', '')
            saml_entity_id = form_data.get('saml_entity_id', '')
            passport_policies = form_data.get('saml_passport_policies', '')
            
            # Save SAML-specific fields
            application.saml_sso_url = saml_sign_on_url
            application.saml_entity_id = saml_entity_id
            application.saml_relay_state = form_data.get('saml_relay_state', '')
            application.saml_username_template = form_data.get('saml_username_template', 'username')
            
            # Process attribute statements
            if 'attribute_name' in form_data:
                attribute_names = form_data.get('attribute_name', [])
                attribute_types = form_data.get('attribute_type', [])
                attribute_values = form_data.get('attribute_value', [])
                
                if not isinstance(attribute_names, list):
                    attribute_names = [attribute_names]
                    attribute_types = [attribute_types]
                    attribute_values = [attribute_values]
                
                for i in range(len(attribute_names)):
                    if i < len(attribute_names) and attribute_names[i]:
                        attr_type = attribute_types[i] if i < len(attribute_types) else 'Unspecified'
                        attr_value = attribute_values[i] if i < len(attribute_values) else ''
                        attribute_statements.append({
                            'name': attribute_names[i],
                            'type': attr_type,
                            'value': attr_value
                        })
            
            # Process group attribute statements
            if 'group_attribute_name' in form_data:
                group_names = form_data.get('group_attribute_name', [])
                group_types = form_data.get('group_attribute_type', [])
                group_filters = form_data.get('group_attribute_filter', [])
                group_values = form_data.get('group_attribute_value', [])
                
                if not isinstance(group_names, list):
                    group_names = [group_names]
                    group_types = [group_types]
                    group_filters = [group_filters]
                    group_values = [group_values]
                
                for i in range(len(group_names)):
                    if i < len(group_names) and group_names[i]:
                        group_type = group_types[i] if i < len(group_types) else 'Unspecified'
                        group_filter = group_filters[i] if i < len(group_filters) else 'equals'
                        group_value = group_values[i] if i < len(group_values) else ''
                        group_statements.append({
                            'name': group_names[i],
                            'type': group_type,
                            'filter': group_filter,
                            'value': group_value
                        })
        
        # Process OIDC specific parameters
        elif app_type == 'OIDC':
            passport_policies = form_data.get('oidc_passport_policies', '')
            
            # Process sign-in URLs
            signin_urls = form_data.get('signin_url[]', [])
            if not isinstance(signin_urls, list):
                signin_urls = [signin_urls]
            oidc_sign_in = [url for url in signin_urls if url]
            
            # Process sign-out URLs
            signout_urls = form_data.get('signout_url[]', [])
            if not isinstance(signout_urls, list):
                signout_urls = [signout_urls]
            oidc_sign_out = [url for url in signout_urls if url]
            
            # Process group claims
            if 'group_claim_name' in form_data:
                claim_names = form_data.get('group_claim_name', [])
                claim_conditions = form_data.get('group_claim_condition', [])
                claim_values = form_data.get('group_claim_value', [])
                
                if not isinstance(claim_names, list):
                    claim_names = [claim_names]
                    claim_conditions = [claim_conditions]
                    claim_values = [claim_values]
                
                for i in range(len(claim_names)):
                    if i < len(claim_names) and claim_names[i]:
                        condition = claim_conditions[i] if i < len(claim_conditions) else 'equals'
                        value = claim_values[i] if i < len(claim_values) else ''
                        oidc_group_claims.append({
                            'name': claim_names[i],
                            'condition': condition,
                            'value': value
                        })
        
        # Save passport policies
        application.passport_policies = passport_policies
        
        # Save additional configuration as JSON
        application.configuration_data = {
            'attribute_statements': attribute_statements,
            'group_statements': group_statements,
            'oidc_sign_in': oidc_sign_in,
            'oidc_group_claims': oidc_group_claims,
            'oidc_sign_out': oidc_sign_out,
            'form_data': form_data  # Store the original form data for reference
        }
        
        # Save the application to the database
        application.save()
        logger.info(f"Application '{app_name}' saved to database with ID: {application.id}")
        
        # Call the main function from app_onboarding.py
        print(f"Starting application onboarding for {app_name} ({app_type})")
        
        try:
            # Call the main function with extracted parameters
            main(
                app_name=app_name,
                app_type=app_type,
                app_owner_email=user.email,
                saml_sign_on_url=saml_sign_on_url,
                saml_entity_id=saml_entity_id,
                passport_policies=passport_policies,
                attribute_statements=attribute_statements,
                group_statements=group_statements,
                oidc_sign_in=oidc_sign_in,
                oidc_group_claims=oidc_group_claims,
                oidc_sign_out=oidc_sign_out
            )
            
            # Update application status to active
            application.status = 'active'
            application.save()
            logger.info(f"Application '{app_name}' status updated to active")
            
            print(f"Application onboarding completed for {app_name}")
        except Exception as e:
            # Update application status to error
            application.status = 'error'
            application.save()
            logger.error(f"Error during onboarding for '{app_name}': {str(e)}")
            print(f"Error during onboarding: {str(e)}")
            raise
            
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        print(f"Error: User with ID {user_id} not found")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    # Check if data is provided as command line argument
    if len(sys.argv) > 2:
        try:
            # Parse the JSON data from command line
            form_data = json.loads(sys.argv[1])
            user_id = int(sys.argv[2])
            process_form_data(form_data, user_id)
        except json.JSONDecodeError:
            print("Error: Invalid JSON data provided")
            sys.exit(1)
        except ValueError:
            print("Error: Invalid user ID provided")
            sys.exit(1)
    else:
        print("Error: Insufficient arguments. Need form data and user ID")
        sys.exit(1)
