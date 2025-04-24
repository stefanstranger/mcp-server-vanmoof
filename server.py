from mcp.server.fastmcp import FastMCP
import requests
from dataclasses import dataclass
from typing import Dict, Any
import os
import base64
from dotenv import load_dotenv
from tzlocal import get_localzone
import locale
from datetime import datetime, timedelta
import re

# Load variables from .env file into the environment
load_dotenv()

# Get the local timezone object
local_tz = get_localzone()

# Get the IANA timezone name (e.g., 'Europe/Amsterdam')
timezone_name = str(local_tz)

# Get the default locale settings (language code, encoding)
lang_code, encoding = locale.getdefaultlocale()

# Create the MCP server
mcp = FastMCP("vanMoof")

# vanMoof API credentials
VANMOOF_USERNAME = os.getenv("VANMOOF_USERNAME")
if not VANMOOF_USERNAME:
    raise ValueError("VANMOOF_USERNAME environment variable is not set.")
VANMOOF_PASSWORD = os.getenv("VANMOOF_PASSWORD")
if not VANMOOF_PASSWORD:
    raise ValueError("VANMOOF_PASSWORD environment variable is not set.")


@dataclass

class VanMoofAPI:
    def get_vanmoof_token(username, password):
        """
        Authenticates with the VanMoof API and retrieves an access token.

        Args:
            username: The user's VanMoof email address.
            password: The user's VanMoof password.

        Returns:
            The access token string if authentication is successful, otherwise None.
        """
        api_key = 'fcb38d47-f14b-30cf-843b-26283f6a5819'
        uri_prefix = 'https://my.vanmoof.com/api/v8'
        auth_url = f'{uri_prefix}/authenticate'

        # Prepare Basic Authentication credentials
        auth_string = f"{username}:{password}"
        encoded_auth_string = base64.b64encode(auth_string.encode('ascii')).decode('ascii')

        headers = {
            'Authorization': f'Basic {encoded_auth_string}',
            'Api-Key': api_key
        }

        try:
            response = requests.post(auth_url, headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            # Parse the JSON response and extract the token
            token = response.json().get('token')
            return token

        except requests.exceptions.RequestException as e:
            print(f"An error occurred during the API request: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None
        
    def get_application_token(token):
        """
        Authenticates with the VanMoof API and retrieves an application token.

        Args:
            token: The user's VanMoof access token.

        Returns:
            The application token string if authentication is successful, otherwise None.
        """
        api_key = 'fcb38d47-f14b-30cf-843b-26283f6a5819'
        uri_prefix = 'https://api.vanmoof-api.com/v8'
        auth_url = f'{uri_prefix}/getApplicationToken'

        headers = {
            'authorization': f'Bearer {token}',
            "accept": "*/*",
            "user-agent": "VanMoof-Rider/23.7 (sdk_gphone_x86_arm, Android 11)",
            'api-key': api_key
        }

        try:
            response = requests.get(auth_url, headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            # Parse the JSON response and extract the token
            application_token = response.json()
            return application_token.get('token')

        except requests.exceptions.RequestException as e:
            print(f"An error occurred during the API request: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    @mcp.tool()
    # Function to get customer data
    def get_customer_data() -> Dict[str, Any]:
        """
        Retrieves customer data from the vanMoof API.

        Returns:
            The rider vanMoof's customer data if authentication is successful, otherwise None.
        """
        # Get the Bearer token from the authenticate method
        token = VanMoofAPI.get_vanmoof_token(VANMOOF_USERNAME, VANMOOF_PASSWORD)
        if not token:
            return {"error": "Authentication failed"}

        url = "https://my.vanmoof.com/api/v8/getCustomerData"
        headers = {
            "authorization": f"Bearer {token}",
            "api-key": "fcb38d47-f14b-30cf-843b-26283f6a5819"
        }
        response = requests.get(url, headers=headers)
        return response.json()

    @mcp.tool()
    # Function to get vanMoof Cities
    def get_vanmoof_cities() -> Dict[str, Any]:
        """
        Retrieves a list of city data from the vanMoof API.

        Returns:
            The rider vanMoof's city data if authentication is successful, otherwise None.        
        """
        # Get the Bearer token from the authenticate method
        token = VanMoofAPI.get_vanmoof_token(VANMOOF_USERNAME, VANMOOF_PASSWORD)
        application_token = VanMoofAPI.get_application_token(token)
        if not application_token:
            return {"error": "Authentication failed"}

        url = "https://tenjin.vanmoof.com/api/v1/cities"
        headers = {
            "authorization": f"Bearer {application_token}",
            "api-key": "fcb38d47-f14b-30cf-843b-26283f6a5819"
        }
        response = requests.get(url, headers=headers)
        return response.json()

    @mcp.tool()
    # Function to get rider preferences
    def get_rider_preferences() -> Dict[str, Any]:
        """
        Retrieves rider preferences from the vanMoof API.

        Returns:
            The rider preferences if authentication is successful, otherwise None.
        """

        # Get the Bearer token from the authenticate method
        token = VanMoofAPI.get_vanmoof_token(VANMOOF_USERNAME, VANMOOF_PASSWORD)
        application_token = VanMoofAPI.get_application_token(token)
        if not application_token:
            return {"error": "Authentication failed"}

        # Get the riderId from the customer data
        # path to rider is data.uuid in the customer data json response
        riderId = VanMoofAPI.get_customer_data().get('data', {}).get('uuid')
        if not riderId:
            return {"error": "RiderId not found"}

        url = f"https://tenjin.vanmoof.com/api/v1/riders/{riderId}/preferences"
        headers = {
            "authorization": f"Bearer {application_token}",
            "api-key": "fcb38d47-f14b-30cf-843b-26283f6a5819"
        }
        response = requests.get(url, headers=headers)
        return response.json()

    #@mcp.tool()
    # def get_weekly_rides(last_seen_week: str = None, limit: int = 5) -> Dict[str, Any]:
    #     """
    #     Retrieves weekly rides from the vanMoof API.

    #     Args:
    #         last_seen_week: The date of the last seen week in format "YYYY-MM-DD".
    #                         If None, uses the current date.
    #         limit: The maximum number of weekly ride results to return. Defaults to 5.

    #     Returns:
    #         The weekly rides if authentication is successful, otherwise None.
    #     """
    #     # Get the Bearer token from the authenticate method
    #     token = VanMoofAPI.get_vanmoof_token(VANMOOF_USERNAME, VANMOOF_PASSWORD)
    #     application_token = VanMoofAPI.get_application_token(token)
    #     if not application_token:
    #         return {"error": "Authentication failed"}

    #     # Get the riderId from the customer data
    #     customerData = VanMoofAPI.get_customer_data()
    #     riderId = customerData.get('data', {}).get('uuid')
    #     if not riderId:
    #         return {"error": "RiderId not found"}
    #     bikeId = customerData.get('data', {}).get('bikes', [{}])[0].get('id')
    #     if not bikeId:
    #         return {"error": "BikeId not found"}
    #     country = customerData.get('data', {}).get('country')
    #     if not country:
    #         return {"error": "CountryCode not found"}

    #     # If last_seen_week is not provided, use current date
    #     if last_seen_week is None:
    #         last_seen_week = datetime.now().strftime("%Y-%m-%d")

    #     # Ensure last_seen_week is the Monday of the week
    #     date_obj = datetime.strptime(last_seen_week, "%Y-%m-%d")
    #     monday = date_obj - timedelta(days=date_obj.weekday())
    #     last_seen_week = monday.strftime("%Y-%m-%d")

    #     url = f"https://tenjin.vanmoof.com/api/v1/rides/{riderId}/{bikeId}/weekly"
    #     querystring = {"lastSeenWeek": last_seen_week, "limit": str(limit)}

    #     headers = {
    #         "authorization": f"Bearer {application_token}",
    #         "api-key": "fcb38d47-f14b-30cf-843b-26283f6a5819",
    #         "cache-control": "no-cache, private",
    #         "accept-language": f"{country.lower()}_{country.upper()}",
    #         "accept-encoding": "gzip",
    #         "timezone": timezone_name,
    #         "accept": "*/*",
    #     }
    #     response = requests.get(url, headers=headers, params=querystring)
    #     return response.json()

    @mcp.tool()
    def get_rides_summary()-> Dict[str, Any]:
        """
        Retrieves total rides summary for the VanMoof rider being authenticated.


        Returns:
            The a summary of the total rides of the VanMoof rider if authentication is successful, otherwise None.
            The following information is returned:
            - Average distance in km
            - Total Rides
            - Average duration in minutes
            - Total distance in km
        """
        # Get the Bearer token from the authenticate method
        token = VanMoofAPI.get_vanmoof_token(VANMOOF_USERNAME, VANMOOF_PASSWORD)
        application_token = VanMoofAPI.get_application_token(token)
        if not application_token:
            return {"error": "Authentication failed"}

        # Get the riderId from the customer data
        customerData = VanMoofAPI.get_customer_data()
        riderId = customerData.get('data', {}).get('uuid')
        if not riderId:
            return {"error": "RiderId not found"}
        bikeId = customerData.get('data', {}).get('bikes', [{}])[0].get('id')
        if not bikeId:
            return {"error": "BikeId not found"}
        country = customerData.get('data', {}).get('country')
        if not country:
            return {"error": "CountryCode not found"}

        last_seen_week = datetime.now().strftime("%Y-%m-%d")

        # Ensure last_seen_week is the Monday of the week
        date_obj = datetime.strptime(last_seen_week, "%Y-%m-%d")
        monday = date_obj - timedelta(days=date_obj.weekday())
        last_seen_week = monday.strftime("%Y-%m-%d")

        url = f"https://tenjin.vanmoof.com/api/v1/rides/{riderId}/{bikeId}/weekly"
        querystring = {"lastSeenWeek": last_seen_week, "limit": str(1)}

        headers = {
            "authorization": f"Bearer {application_token}",
            "api-key": "fcb38d47-f14b-30cf-843b-26283f6a5819",
            "cache-control": "no-cache, private",
            "accept-language": f"{country.lower()}_{country.upper()}",
            "accept-encoding": "gzip",
            "timezone": timezone_name,
            "accept": "*/*",
        }
        response = requests.get(url, headers=headers, params=querystring)
        return response.json().get('carousel', {}).get('summary', {})

    @mcp.tool()
    def get_rides_for_week(date_in_week: str = "") -> Dict[str, Any]:
        """
        Retrieves rides for a specific week from the vanMoof API.
        
        Args:
            date_in_week: Any date within the week in format "YYYY-MM-DD".
                        If None, uses the current date.
                        
        Returns:
            The rides for the specified week if authentication is successful, otherwise None.
        """
        
        # If date_in_week is not provided, return error
        if date_in_week == "":
            return {"error": "Missing Argument. Please use YYYY-MM-DD format."}
        # Validate date format (YYYY-MM-DD)
        try:
            # Check basic format with regex
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_in_week):
                return {"error": "Invalid date format. Please use YYYY-MM-DD format."}
            
            # Try to parse the date to validate it's a real date
            date_obj = datetime.strptime(date_in_week, "%Y-%m-%d")
        except ValueError:
            return {"error": "Invalid date. Please provide a valid date in YYYY-MM-DD format."}
        
        # Get the Bearer token from the authenticate method
        token = VanMoofAPI.get_vanmoof_token(VANMOOF_USERNAME, VANMOOF_PASSWORD)
        application_token = VanMoofAPI.get_application_token(token)
        if not application_token:
            return {"error": "Authentication failed"}
        
        # Get the riderId and bikeId from the customer data
        customerData = VanMoofAPI.get_customer_data()
        riderId = customerData.get('data', {}).get('uuid')
        if not riderId:
            return {"error": "RiderId not found"}
        bikeId = customerData.get('data', {}).get('bikes', [{}])[0].get('id')
        if not bikeId:
            return {"error": "BikeId not found"}
        country = customerData.get('data', {}).get('country')
        if not country:
            return {"error": "CountryCode not found"}    
        
        # Calculate the Monday (start) and Sunday (end) of the week
        monday = date_obj - timedelta(days=date_obj.weekday())
        sunday = monday + timedelta(days=7)
        
        # The API needs the end date of the week as lastSeenWeek
        last_seen_week = sunday.strftime("%Y-%m-%d")
        
        url = f"https://tenjin.vanmoof.com/api/v1/rides/{riderId}/{bikeId}/weekly"
        querystring = {"lastSeenWeek": last_seen_week, "limit": "1"}
        
        headers = {
            "authorization": f"Bearer {application_token}",
            "api-key": "fcb38d47-f14b-30cf-843b-26283f6a5819",
            "cache-control": "no-cache, private",
            "accept-language": f"{country.lower()}_{country.upper()}",
            "accept-encoding": "gzip",
            "timezone": timezone_name,
            "accept": "*/*",
        }
        
        response = requests.get(url, headers=headers, params=querystring)
        
        result = response.json().get('section', {})[0]
        # add section querystring to the result json
        result['querystring'] = querystring    
        
        if not result:
            return {"error": "No rides found for the specified week"}
        else:
            return result
        
    @mcp.tool()
    def get_city_rides_thisweek()-> Dict[str, Any]:
        """
        Retrieves total city rides summary from VanMoof riders.


        Returns:
            The a summary of the total rides of the VanMoof rider city if authentication is successful, otherwise None.
            The following information is returned:
            - City name
            - Average distance in km
            - Total Rides
            - Average duration in minutes
            - Location in latitude and longitude
        """
        # Get the Bearer token from the authenticate method
        token = VanMoofAPI.get_vanmoof_token(VANMOOF_USERNAME, VANMOOF_PASSWORD)
        application_token = VanMoofAPI.get_application_token(token)
        if not application_token:
            return {"error": "Authentication failed"}

        # Get the riderId from the customer data
        customerData = VanMoofAPI.get_customer_data()
        riderId = customerData.get('data', {}).get('uuid')
        if not riderId:
            return {"error": "RiderId not found"}
        bikeId = customerData.get('data', {}).get('bikes', [{}])[0].get('id')
        if not bikeId:
            return {"error": "BikeId not found"}
        country = customerData.get('data', {}).get('country')
        if not country:
            return {"error": "CountryCode not found"}
        
        # Get the riders preferences and city
        riderPreferences = VanMoofAPI.get_rider_preferences()
        riderCity = riderPreferences.get('city')
        # Get city name from the city code
        cities = VanMoofAPI.get_vanmoof_cities()
        location= next((city['location'] for city in cities if city['code'] == riderCity), None)

        last_seen_week = datetime.now().strftime("%Y-%m-%d")

        # Ensure last_seen_week is the Monday of the week
        date_obj = datetime.strptime(last_seen_week, "%Y-%m-%d")
        monday = date_obj - timedelta(days=date_obj.weekday())
        last_seen_week = monday.strftime("%Y-%m-%d")

        url = f"https://tenjin.vanmoof.com/api/v1/rides/{riderId}/{bikeId}/weekly"
        querystring = {"lastSeenWeek": last_seen_week, "limit": str(1)}

        headers = {
            "authorization": f"Bearer {application_token}",
            "api-key": "fcb38d47-f14b-30cf-843b-26283f6a5819",
            "cache-control": "no-cache, private",
            "accept-language": f"{country.lower()}_{country.upper()}",
            "accept-encoding": "gzip",
            "timezone": timezone_name,
            "accept": "*/*",
        }
        response = requests.get(url, headers=headers, params=querystring)
        

        result = response.json().get('carousel', {}).get('city', {})
        # Convert the average duration from milliseconds to minutes.
        result['averageDuration'] = round(result['averageDuration'] / 1000 / 60, 2)
        # Add the city name to the result
        result['location'] = location
            
        return result

    @mcp.tool()
    def get_world_rides_thisweek()-> Dict[str, Any]:
        """
        Retrieves total world rides summary from VanMoof riders.


        Returns:
            The a summary of the total rides of the VanMoof rider city if authentication is successful, otherwise None.
            The following information is returned:
            - Average distance in km
            - Total Rides
            - Average duration in minutes
        """
        # Get the Bearer token from the authenticate method
        token = VanMoofAPI.get_vanmoof_token(VANMOOF_USERNAME, VANMOOF_PASSWORD)
        application_token = VanMoofAPI.get_application_token(token)
        if not application_token:
            return {"error": "Authentication failed"}

        # Get the riderId from the customer data
        customerData = VanMoofAPI.get_customer_data()
        riderId = customerData.get('data', {}).get('uuid')
        if not riderId:
            return {"error": "RiderId not found"}
        bikeId = customerData.get('data', {}).get('bikes', [{}])[0].get('id')
        if not bikeId:
            return {"error": "BikeId not found"}
        country = customerData.get('data', {}).get('country')
        if not country:
            return {"error": "CountryCode not found"}

        last_seen_week = datetime.now().strftime("%Y-%m-%d")

        # Ensure last_seen_week is the Monday of the week
        date_obj = datetime.strptime(last_seen_week, "%Y-%m-%d")
        monday = date_obj - timedelta(days=date_obj.weekday())
        last_seen_week = monday.strftime("%Y-%m-%d")

        url = f"https://tenjin.vanmoof.com/api/v1/rides/{riderId}/{bikeId}/weekly"
        querystring = {"lastSeenWeek": last_seen_week, "limit": str(1)}

        headers = {
            "authorization": f"Bearer {application_token}",
            "api-key": "fcb38d47-f14b-30cf-843b-26283f6a5819",
            "cache-control": "no-cache, private",
            "accept-language": f"{country.lower()}_{country.upper()}",
            "accept-encoding": "gzip",
            "timezone": timezone_name,
            "accept": "*/*",
        }
        response = requests.get(url, headers=headers, params=querystring)    

        result = response.json().get('carousel', {}).get('world', {})
        # Convert the average duration from milliseconds to minutes.
        result['averageDuration'] = round(result['averageDuration'] / 1000 / 60, 2)
            
        return result