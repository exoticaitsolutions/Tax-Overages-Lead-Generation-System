import json
import requests
import time
from config import *
from utils import mask_password, modification_the_json, update_json_file, read_json_file
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)
from urllib.parse import urlparse, parse_qs
from web_driver import initialize_driver


def generate_new_code_via_login():
    driver = None
    try:
        driver = initialize_driver(NEW_EVENT_LOOP)
        url = f"{API_BASE_URL}/oauth/index?client_id={CLIENT_ID}&redirect_uri={CALL_BACK_URL}&response_type=code"
        print("Opening URL:", url)

        driver.get(url)
        time.sleep(3)

        username_element = driver.find_element(By.XPATH, '//*[@id="username"]')
        username_element.send_keys(PHONE_BURNER_USER_NAME)
        print(f"Entered username: {PHONE_BURNER_USER_NAME}")

        password_element = driver.find_element(By.XPATH, '//*[@id="password"]')
        password_element.send_keys(PHONE_BURNER_PASSWORD)
        print(f"Entered password: {mask_password(PHONE_BURNER_PASSWORD)}")

        driver.find_element(By.XPATH, '//*[@id="oauth_signin"]/button/div').click()
        time.sleep(3)

        approve_button = driver.find_element(By.XPATH, '//*[@id="approve"]')
        approve_button.click()
        time.sleep(5)

        current_url = driver.current_url
        query_params = parse_qs(urlparse(current_url).query)
        code = query_params.get("code", [None])[0]
        print("Extracted code:", code)
        return True, code
    except (
        NoSuchElementException,
        StaleElementReferenceException,
        WebDriverException,
    ) as e:
        print(f"Error during login process: {e}")
        return False, "Internal Error Occurred during login. Please Try Again!!"
    finally:
        if driver:
            driver.quit()


def generate_new_refresh_token():
    try:
        auth_code = read_json_file("token.json").get("code")
        payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": CALL_BACK_URL,
            "grant_type": "authorization_code",
            "code": auth_code,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.post(
            "https://www.phoneburner.com/oauth/accesstoken",
            data=payload,
            headers=headers,
        )

        if response.status_code == 400:
            print("Generating code via login process")
            success, login_code = generate_new_code_via_login()
            if success:
                payload["code"] = login_code
                update_json_file({"code": login_code})
                response = requests.post(
                    "https://www.phoneburner.com/oauth/accesstoken",
                    data=payload,
                    headers=headers,
                )

        if response.status_code == 200:
            data = response.json()
            update_json_file(
                {
                    "access_token": data.get("access_token"),
                    "refresh_token": data.get("refresh_token"),
                }
            )
            return True
        return False
    except requests.RequestException as e:
        print(f"Network error during token generation: {e}")
        return False
    except ValueError as e:
        print(f"Error decoding response data: {e}")
        return False


def validate_and_generate_new_token():

# Write the data to token.json
    with open('token.json', 'w') as json_file:
        json.dump({
        "code": "",
        "access_token": "",
        "refresh_token": ""
    }, json_file, indent=4)
    try:
        test_url = f"{API_BASE_URL}/rest/1/members/{PHONE_BURNER_USER_ID}"
        access_token = read_json_file("token.json").get("access_token")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        response = requests.get(test_url, headers=headers)

        if response.status_code == 401:
            print("Invalid token, generating new token via refresh token...")
            refresh_token = read_json_file("token.json").get("refresh_token")
            payload = {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }
            token_response = requests.post(
                f"{API_BASE_URL}/oauth/refreshtoken", data=payload
            )

            if token_response.status_code == 200:
                token_data = token_response.json()
                if "error" in token_data:
                    print("Error in refresh token response:", token_data.get("error"))
                    return generate_new_refresh_token()
                update_json_file({"access_token": token_data.get("access_token")})
                return True
        else:
            return True
    except requests.RequestException as e:
        print(f"Network error during token validation: {e}")
        return False
    except ValueError as e:
        print(f"Error decoding token response: {e}")
        return False


def integration_with_phoneburner_crm(json_data_str, output_text):
    try:
        if validate_and_generate_new_token():
            access_token = read_json_file("token.json").get("access_token")
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            new_json, data_length = modification_the_json(json_data_str)
            count = 0
            for index, payload_data in enumerate(new_json):
                payload = json.dumps(payload_data)
                response = requests.post(
                    f"{API_BASE_URL}/rest/1/contacts/", headers=headers, data=payload
                )
                if response.status_code == 201:
                    count += 1
                    print(f"Successfully inserted item {index + 1}/{data_length}")
                else:
                    print(
                        f"Failed to insert item {index + 1}/{data_length}: {response.text}"
                    )
            success_message = f"Successfully inserted {count} out of {data_length} items into Phone Burner CRM."
            return True, success_message
        return (
            False,
            "Internal Error Occurred during token validation. Please Try Again!!",
        )
    except (ValueError, json.JSONDecodeError) as e:
        print(f"Data processing error: {e}")
        return False, f"Data processing error: {e}. Please check the JSON data format."
    except requests.RequestException as e:
        print(f"Network error during CRM integration: {e}")
        return False, "Network error during CRM integration. Please try again."
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False, "Internal Error Occurred. Please Try Again!!"
