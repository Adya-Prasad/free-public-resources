The function handling API-related functionality in your code is:
lookup(symbol)

    Purpose: Fetches stock information for a given stock symbol by making an API request to https://finance.cs50.io/quote.
    Steps in the Function:
        API URL Construction:

url = f"https://finance.cs50.io/quote?symbol={symbol.upper()}"

    Converts the stock symbol to uppercase and appends it to the URL as a query parameter.

API Request:

response = requests.get(url)
response.raise_for_status()

    Makes a GET request to the API.
    Uses raise_for_status to handle HTTP errors (e.g., 404 or 500).

Parse the JSON Response:

quote_data = response.json()
return {
    "name": quote_data["companyName"],
    "price": quote_data["latestPrice"],
    "symbol": symbol.upper()
}

    Extracts key details (companyName, latestPrice, symbol) from the response JSON.
    Returns a dictionary containing this data.

Error Handling:

    Handles requests.RequestException for network issues.
    Handles KeyError or ValueError for parsing issues.
    If an error occurs, the function returns None.
