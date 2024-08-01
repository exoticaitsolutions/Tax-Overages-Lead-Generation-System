import json
import requests
from config import ACCESS_TOKEN, API_BASE_URL
from utils import modification_the_json, print_the_output_statement


def intergation_with_phoneburner_crn(json_data_str, output_text):
    print_the_output_statement(output_text, "Inserting data into Phone Burner CRM...")
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        new_json, data_length = modification_the_json(json_data_str)
        count = 0
        for index, payload_data in enumerate(new_json):
            payload = json.dumps(payload_data)
            try:
                response = requests.post(
                    f"{API_BASE_URL}/rest/1/contacts/", headers=headers, data=payload
                )
                response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
                if response.status_code == 201:
                    count += 1
                    print(f"Successfully inserted item {index + 1}/{data_length}")
                else:
                    print(
                        f"Failed to insert item {index + 1}/{data_length}: {response.text}"
                    )
            except requests.RequestException as e:
                print(f"Network error for item {index + 1}/{data_length}: {e}")
                # You might want to continue with the next item or decide on error handling strategy
                continue
        success_message = f"Successfully inserted {count} out of {data_length} items into Phone Burner CRM."
        return True, success_message
    except ValueError as e:
        # Handle JSON encoding/decoding errors specifically
        return False, f"Data processing error: {e}. Please check the JSON data format."
    except Exception as e:
        # Handle other unexpected errors
        return False, f"An unexpected error occurred: {e}. Please try again later."
