# ================================================
# FILE: common/utils.py
# PURPOSE: Shared helper functions for the application
# ================================================
import requests
import json
from .config import logger, MARKET_CURRENCY_CONFIG

def split_message_for_slack(message: str, max_length: int = 2800) -> list:
    """Splits a long message into chunks suitable for Slack, respecting newlines."""
    if not message: return []
    if len(message) <= max_length: return [message]
    
    chunks, current_chunk = [], ""
    for line in message.split('\n'):
        if len(current_chunk) + len(line) + 1 > max_length:
            if current_chunk.strip(): chunks.append(current_chunk)
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"
    if current_chunk.strip(): chunks.append(current_chunk)
    return chunks

def query_api(url: str, payload: dict, endpoint_name: str) -> dict:
    """Sends a POST request to the specified API endpoint and handles errors."""
    logger.info(f"Querying {endpoint_name} API at {url} with payload: {json.dumps(payload)}")
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"{endpoint_name} API Connection Error: {e}")
        return {"error": f"Could not connect to the {endpoint_name} API."}

def get_currency_info(market: str) -> dict:
    """Retrieves currency configuration for a given market."""
    return MARKET_CURRENCY_CONFIG.get(str(market).upper(), {'rate': 1.0, 'symbol': '€', 'name': 'EUR'})

def format_currency(amount, market: str) -> str:
    """Formats a numeric amount into a currency string with the correct symbol and formatting."""
    currency_info = get_currency_info(market)
    symbol = currency_info['symbol']
    try:
        safe_amount = float(amount or 0.0)
        if currency_info['name'] in ['SEK', 'NOK', 'DKK']:
            return f"{safe_amount:,.0f} {symbol}"
        else:
            return f"{symbol}{safe_amount:,.2f}"
    except (ValueError, TypeError):
        return f"{symbol}0.00"

def convert_eur_to_local(amount_eur, market: str) -> float:
    """Converts a EUR amount to the local currency amount for a given market."""
    try:
        safe_amount = float(amount_eur if amount_eur is not None else 0.0)
    except (ValueError, TypeError):
        safe_amount = 0.0
    return safe_amount * get_currency_info(market)['rate']
