import os
import sys
import re
import subprocess

affected_areas = {
    "Devtron dashboard completely down": 100,
    "Login issues": 50,
    "RBAC Issues": 40,
    "CI": 50,
    "CD": 50,
    "App creation": 30,
    "Deployment from Chart store": 40,
    "Security features": 50,
    "CI/CD Plugins": 30,
    "Other CRITICAL functionality": 30,
    "Other NON-CRITICAL functionality": 20,
    "None": 0
}

additional_affected_areas = {
    "Devtron dashboard completely down": 100,
    "Login issues": 50,
    "RBAC Issues": 40,
    "CI": 50,
    "CD": 50,
    "App creation": 30,
    "Deployment from Chart store": 40,
    "Security features": 50,
    "CI/CD Plugins": 30,
    "Other CRITICAL functionality": 30,
    "Other NON-CRITICAL functionality": 20,
    "None": 0
}

prod_environment = {
    "Prod": 2,
    "Non-prod": 1,
    "None": 1
}

user_unblocked = {
    "Yes": 1,
    "No": 2,
    "None": 1
}

user_unblocked_reason = {
    "TEMPORARILY - By disabling a CRITICAL functionality": 3,
    "TEMPORARILY - By disabling a NON-CRITICAL functionality": 1.2,
    "TEMPORARILY - By doing some changes from the backend/DB": 1,
    "PERMANENTLY - By giving a workaround (From outside Devtron)": 2,
    "PERMANENTLY - By giving a workaround (Within Devtron)": 1,
    "None": 1
}

def process_issue_body(issue_body, pagerduty_score_threshold):
    affected_areas_pattern = r'###\s*Affected\s*areas\s*\n\n(.*?)\n\n###'
    additional_affected_areas_pattern = r'###\s*Additional\s*affected\s*areas\s*\n\n(.*?)\n\n###'
    prod_non_prod_pattern = r'###\s*Prod/Non-prod\s*environments\?\s*\n\n(.*?)\n\n###'
    user_unblocked_pattern = r'###\s*Is\s*User\s*unblocked\?\s*\n\n(.*?)\n\n###'
    user_unblocked_reason_pattern = r'###\s*How\s*was\s*the\s*user\s*un-blocked\?\s*\n\n(.*?)\n\n###'

    affected_areas_match = re.search(affected_areas_pattern, issue_body)
    additional_affected_areas_match = re.search(additional_affected_areas_pattern, issue_body)
    prod_non_prod_match = re.search(prod_non_prod_pattern, issue_body)
    user_unblocked_match = re.search(user_unblocked_pattern, issue_body)
    user_unblocked_reason_match = re.search(user_unblocked_reason_pattern, issue_body)

    affected_area_value = affected_areas_match.group(1).strip() if affected_areas_match else "None"
    additional_affected_area_value = additional_affected_areas_match.group(1).strip() if additional_affected_areas_match else "None"
    prod_non_prod_value = prod_non_prod_match.group(1).strip() if prod_non_prod_match else "None"
    user_unblocked_value = user_unblocked_match.group(1).strip() if user_unblocked_match else "None"
    user_unblocked_reason_value = user_unblocked_reason_match.group(1).strip() if user_unblocked_reason_match else "None"

    affected_areas_score = affected_areas.get(affected_area_value, 0)
    additional_affected_areas_score = additional_affected_areas.get(additional_affected_area_value, 0)
    prod_non_prod_score = prod_environment.get(prod_non_prod_value, 1)
    user_unblocked_score = user_unblocked.get(user_unblocked_value, 1)
    user_unblocked_reason_score = user_unblocked_reason.get(user_unblocked_reason_value, 1)

    print("Affected areas:", affected_area_value)
    print("Additional affected areas:", additional_affected_area_value)
    print("Prod/Non-prod environments?:", prod_non_prod_value)
    print("Is User unblocked?:", user_unblocked_value)
    print("How was the user un-blocked?:", user_unblocked_reason_value)

    if affected_areas_score == 0 or prod_non_prod_score == 0 or user_unblocked_score == 0:
        print("One or more required values are missing. Exiting...")
        sys.exit(0)

    if user_unblocked_reason_score == 0:
        user_unblocked_reason_score = 1

    if user_unblocked_reason_score == 3 or affected_areas_score == 100:
        try:
            result = subprocess.run(['gh', 'issue', 'edit', str(issue_number), '--add-label', 'urgent'], capture_output=True, check=True, text=True)
            print("urgent label added to issue", issue_number)
        except subprocess.CalledProcessError as e:
            print(e.stderr)

    final_score = affected_areas_score + additional_affected_areas_score * prod_non_prod_score * user_unblocked_score * user_unblocked_reason_score
    print("Final Score:", final_score)

    comment = f"Final Score: {final_score}"
    try:
        result1 = subprocess.run(['gh', 'issue', 'comment', str(issue_number), '--body', comment], capture_output=True, check=True, text=True)
        print("Final score commented on issue", issue_number)
    except subprocess.CalledProcessError as e:
        print(e.stderr)

    return final_score

token = os.environ.get('MY_ACCESS_TOKEN')
subprocess.run(['gh', 'auth', 'login', '--with-token'], input=token, text=True, capture_output=True)

issue_body = os.environ.get('ISSUE_BODY')
issue_number = os.environ.get('ISSUE_NUMBER')
pagerduty_score_threshold = os.environ.get('PAGERDUTY_SCORE_THRESHOLD')

final_score = process_issue_body(issue_body, pagerduty_score_threshold)

if final_score <= int(pagerduty_score_threshold):
    try:
        result = subprocess.run(['gh', 'issue', 'edit', str(issue_number), '--remove-label', 'pager-duty'])
        print("pager-duty label removed from issue", issue_number)
    except subprocess.CalledProcessError as e:
        print(e)
