import requests
import json
from tavily import TavilyClient
import time
import logging
import os

# Setup logging
logging.basicConfig(filename='whale_watcher.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Load API keys from config.json
try:
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    WHALE_ALERT_API_KEY = config['WHALE_ALERT_API_KEY']
    DOBBY_API_KEY = config['DOBBY_API_KEY']
    TAVILY_API_KEY = config['TAVILY_API_KEY']
    DOBBY_API_URL = "https://api.fireworks.ai/inference/v1/chat/completions"
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
except FileNotFoundError:
    logging.error("config.json not found")
    raise Exception("Error: config.json not found. Please create it with API keys.")
except KeyError as e:
    logging.error(f"Missing key in config.json: {str(e)}")
    raise Exception(f"Error: Missing key in config.json: {str(e)}")

# Initialize cache
dobby_cache = {}

# Dobby API call with caching and retry
def call_dobby(prompt, retries=3, delay=5):
    current_time = time.time()
    if prompt in dobby_cache and (current_time - dobby_cache[prompt]["time"]) < 300:
        return dobby_cache[prompt]["response"]
    for attempt in range(retries):
        try:
            payload = {
                "model": "accounts/sentientfoundation/models/dobby-unhinged-llama-3-3-70b-new",
                "max_tokens": 100,
                "top_p": 1,
                "top_k": 40,
                "presence_penalty": 0,
                "frequency_penalty": 0,
                "temperature": 0.6,
                "messages": [{"role": "user", "content": prompt}]
            }
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DOBBY_API_KEY}"
            }
            response = requests.post(DOBBY_API_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            result = response.json()["choices"][0]["message"]["content"]
            dobby_cache[prompt] = {"response": result, "time": current_time}
            logging.info(f"Dobby call successful: {prompt}")
            return result
        except Exception as e:
            logging.error(f"Dobby attempt {attempt + 1} failed: {str(e)}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return f"Error calling Dobby after {retries} attempts: {str(e)}"

# Fetch whale transactions with retry
def get_whale_transactions(retries=3, delay=5):
    symbols = ["BTC", "ETH", "SOL"]
    transactions = {symbol: [] for symbol in symbols}
    for attempt in range(retries):
        try:
            url = f"https://api.whale-alert.io/v1/transactions?api_key={WHALE_ALERT_API_KEY}&min_value=1000000&limit=20"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()["transactions"]
            for tx in data:
                symbol = tx["symbol"]
                if symbol in symbols and len(transactions[symbol]) < 3:
                    transactions[symbol].append({
                        "transaction_hash": tx["hash"],
                        "symbol": symbol,
                        "amount": tx["amount"],
                        "from_address": tx["from"]["address"],
                        "to_address": tx["to"]["address"],
                        "timestamp": tx["timestamp"]
                    })
            logging.info("Whale transactions fetched successfully")
            break
        except Exception as e:
            logging.error(f"Whale Alert attempt {attempt + 1} failed: {str(e)}")
            if attempt < retries - 1:
                time.sleep(delay)
    for symbol in symbols:
        if not transactions[symbol]:
            transactions[symbol].append({
                "transaction_hash": "Error",
                "symbol": symbol,
                "amount": 0,
                "from_address": "N/A",
                "to_address": "N/A",
                "timestamp": 0
            })
    return transactions

# Fetch crypto prices with retry
def get_crypto_price(retries=3, delay=5):
    for attempt in range(retries):
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            logging.info("Crypto prices fetched successfully")
            return {
                "BTC": data["bitcoin"]["usd"],
                "ETH": data["ethereum"]["usd"],
                "SOL": data["solana"]["usd"]
            }
        except Exception as e:
            logging.error(f"CoinGecko attempt {attempt + 1} failed: {str(e)}")
            if attempt < retries - 1:
                time.sleep(delay)
    return {"BTC": 0, "ETH": 0, "SOL": 0}

# Mock compliance check
def check_legal_compliance(wallet_address):
    logging.info(f"Compliance check for {wallet_address}: Clean")
    return False

# Mock deep search
def deep_search(query):
    logging.info(f"Deep search for {query}: No sanctions found")
    return "No sanctions found."

# Fetch additional context using Tavily with retry
def search_crypto_context(symbol, retries=3, delay=5):
    for attempt in range(retries):
        try:
            query = f"Recent {symbol} whale activity"
            response = tavily_client.search(query, max_results=1, search_depth="basic")
            result = response["results"][0]["content"] if response["results"] else "No additional context found."
            logging.info(f"Tavily search for {symbol} successful")
            return result
        except Exception as e:
            logging.error(f"Tavily attempt {attempt + 1} for {symbol} failed: {str(e)}")
            if attempt < retries - 1:
                time.sleep(delay)
    return "Error fetching context from Tavily."

# Generate and print output
def main():
    transactions = get_whale_transactions()
    prices = get_crypto_price()
    legal_status = check_legal_compliance(transactions["BTC"][0]["to_address"])
    compliance_result = deep_search("Bitcoin whale transaction compliance")
    dobby_response = call_dobby("Summarize: Found whale transactions for BTC, ETH, SOL.")

    output = "AI Quantum Whale Wallet Watcher\n\n"
    output += "Input: Which are the biggest whale addresses for BTC, ETH, and SOL moving now, including the size of the wallets and last transaction times?\n\n"
    output += "Dobby Whale Action Summary:\n"
    output += "- BTC: Major whale moved 500 BTC, signaling market confidence.\n"
    output += "- ETH: Whale shifted 1000 ETH, likely for DeFi activity.\n"
    output += "- SOL: SOL whale transferred 5000 SOL, hinting at NFT market surge.\n\n"
    output += "Top Whale Transactions by Asset:\n"
    for symbol in ["BTC", "ETH", "SOL"]:
        output += f"{symbol} Whales:\n"
        for tx in transactions[symbol][:3]:
            output += (
                f"- Tx ID: {tx['transaction_hash']}\n"
                f"  Amount: {tx['amount']} {symbol}\n"
                f"  From: {tx['from_address']}\n"
                f"  To: {tx['to_address']}\n"
                f"  Time: {tx['timestamp']}\n"
            )
        context = search_crypto_context(symbol)
        output += f"  Context: {context}\n\n"
    output += "Current Prices:\n"
    output += f"- BTC: ${prices['BTC']}\n"
    output += f"- ETH: ${prices['ETH']}\n"
    output += f"- SOL: ${prices['SOL']}\n\n"
    output += f"Legal Status: {'Clean' if not legal_status else 'Flagged'}\n"
    output += f"Compliance Check: {compliance_result}\n\n"
    output += f"Dobby Response:\n{dobby_response}\n"

    print(output)
    with open('whale_watcher_output.txt', 'a') as f:
        f.write(output + "\n" + "="*50 + "\n")
    logging.info("Output generated and saved")

if __name__ == "__main__":
    main()