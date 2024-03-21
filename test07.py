import re
import requests
import subprocess
import os
import sys

def process_issue_body(body, pagerduty_score_threshold):
    affected_areas_pattern = r'###\s*Affected\s*areas\s*.*?\((.*?)\)'
    additional_affected_areas_pattern = r'###\s*Additional\s*affected\s*areas\s*.*?\((.*?)\)'
    prod_non_prod_pattern = r'###\s*Prod/Non-prod\s*environments\?\s*.*?\(x(\d+)\)'
    user_unblocked_pattern = r'###\s*Is\s*User\s*unblocked\?\s*.*?\(x(\d+)\)'
    user_unblocked_reason_pattern = r'###\s*How\s*was\s*the\s*user\s*un-blocked\?\s*.*?\(x(\d+)\)'

    affected_areas_match = re.search(affected_areas_pattern, body, re.IGNORECASE)
    additional_affected_areas_match = re.search(additional_affected_areas_pattern, body, re.IGNORECASE)
    prod_non_prod_match = re.search(prod_non_prod_pattern, body, re.IGNORECASE)
    user_unblocked_match = re.search(user_unblocked_pattern, body, re.IGNORECASE)
    user_unblocked_reason_match = re.search(user_unblocked_reason_pattern, body, re.IGNORECASE)

    affected_areas = int(affected_areas_match.group(1).strip()) if affected_areas_match else 0
    additional_affected_areas = int(additional_affected_areas_match.group(1).strip()) if additional_affected_areas_match else 0
    prod_non_prod = int(prod_non_prod_match.group(1).strip()) if prod_non_prod_match else 0
    user_unblocked = int(user_unblocked_match.group(1).strip()) if user_unblocked_match else 0
    user_unblocked_reason = int(user_unblocked_reason_match.group(1).strip()) if user_unblocked_reason_match else 0
    
    print("Issue Body:", body)
    print("Affected areas:", affected_areas)
    print("Additional affected areas:", additional_affected_areas)
    print("Prod/Non-prod environments?:", prod_non_prod)
    print("Is User unblocked?:", user_unblocked)
    print("How was the user un-blocked?:", user_unblocked_reason)
    print("\n")
    
    if any(value == 0 for value in [affected_areas, prod_non_prod, user_unblocked]):
        print("One or more required values are missing. Exiting...")
        sys.exit(0)
    

    if user_unblocked_reason == 0:
        user_unblocked_reason=1
    print("user_unblocked_reason")
    
    
    if user_unblocked_reason == 3:
            try:
                result = subprocess.run(['gh', 'issue', 'edit', str(issue["number"]), '--add-label', 'urgent'], capture_output=True, check=True, text=True)
                print("urgent label added to issue", issue["number"])
            except subprocess.CalledProcessError as e:
                print(e.stderr)
   
    final_score = (affected_areas + additional_affected_areas) * prod_non_prod * user_unblocked * user_unblocked_reason
    print("Final Score:", final_score)
    
    comment = f"Final Score: {final_score}"
    try:
        result1 = subprocess.run(['gh', 'issue', 'comment', str(issue["number"]), '--body', comment], capture_output=True, check=True, text=True)
        print("Final score commented on issue", issue["number"])
    
    except subprocess.CalledProcessError as e:
        print(e.stderr)

    return final_score

url = "https://api.github.com/repos/demoDVTNorg/devtro/issues"
params = {
    "labels": "bug",
    "state": "open"
}

response = requests.get(url, params=params)
pagerduty_score_threshold = 300

if response.status_code == 200:
    issues = response.json()

    for issue in issues:
        body = issue["body"]
        final_score = process_issue_body(body, pagerduty_score_threshold)
        
        if final_score <= pagerduty_score_threshold:
            try: 
                result=subprocess.run(['gh', 'issue', 'edit', str(issue["number"]), '--remove-label', 'bug'])
                print("bug label removed from issue", issue["number"])

            except subprocess.CalledProcessError as e:
                print(e) 
    

else:
    print("Failed to fetch issues:", response.text)

