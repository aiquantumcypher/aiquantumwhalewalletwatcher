# AI Quantum Whale Wallet Watcher

## Overview
The AI Quantum Whale Wallet Watcher is an open-source tool that monitors large cryptocurrency transactions (whales) for Bitcoin (BTC), Ethereum (ETH), and Solana (SOL). It uses Whale Alert for transaction data, CoinGecko for prices, Tavily for context, and Dobby API for summarization, with mock compliance checks. The script is designed for reliable server execution, logging results for extended evaluations.

## Features
- Tracks whale transactions (≥ $1M) for BTC, ETH, and SOL.
- Fetches real-time market prices from CoinGecko.
- Provides context on whale activity via Tavily search.
- Summarizes findings using Dobby API.
- Includes mock compliance and sanction checks.
- Logs execution details to `whale_watcher.log` and outputs to `whale_watcher_output.txt`.

## Setup
1. Ensure Python 3.6+ and pip are installed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt