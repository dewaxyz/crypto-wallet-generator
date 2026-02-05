"""
- Crypto wallet generator that creates random BIP39 mnemonics and checks balances.
- Checks balances on Ethereum, Dogecoin, and BNB networks using high-speed async requests.
- Made by XieyeT AKA dewaxyz AKA Dewa M
"""
import asyncio
import os
import sys
import time
from datetime import datetime

import aiohttp
import requests
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from colorthon import Colors

RED = Colors.RED
GREEN = Colors.GREEN
CYAN = Colors.CYAN
YELLOW = Colors.YELLOW
RESET = Colors.RESET


def set_terminal_title(title: str):
    if os.name == "nt":
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW(title)
    else:
        sys.stdout.write(f"\x1b]2;{title}\x07")
        sys.stdout.flush()


def clear_console():
    os.system("cls") if 'win' in sys.platform.lower() else os.system("clear")


# API ETH Conversion
def get_usd_rate(amount: float, ticker_url: str) -> int:
    try:
        response = requests.get(ticker_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            rate = data.get("rates", {}).get("usd", 0)
            time.sleep(1)
            return int(amount * rate)
    except Exception:
        pass
    return 0


# API DOGE Conversion
def get_doge_usd_rate(doge_amount: float) -> int:
    url = "https://dogecoin.atomicwallet.io/api/v2/tickers/?currency=usd"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            rate = data.get("rates", {}).get("usd", 0)
            time.sleep(1)
            return int(doge_amount * rate)
    except Exception:
        pass
    return 0


# API BNB Conversion
def get_bnb_usd_rate(bnb_amount: float) -> int:
    url = "https://bsc-nn.atomicwallet.io/api/v2/tickers/?currency=usd"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            rate = data.get("rates", {}).get("usd", 0)
            time.sleep(1)
            return int(bnb_amount * rate)
    except Exception:
        pass
    return 0


def save_found_wallet(network, address, balance, mnemonic, private_key):
    """Save found wallet details to a timestamped file in found_wallets folder."""
    if not os.path.exists("found_wallets"):
        os.makedirs("found_wallets")

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"found_wallets/balance_found_{timestamp}.txt"

    with open(filename, "w") as file:
        file.write(f"Mnemonic Phrase: {mnemonic}\n\n")
        file.write("Found Balances:\n")
        file.write(f"Network: {network}, Address: {address}, Balance: {balance}\n")
        file.write(f"Private Key: {private_key}\n")

    print(f"Balance information saved to {filename}")


def generate_wallet_addresses(seed_bytes: bytes) -> tuple[str, str]:
    eth_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
    eth_addr = eth_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0).PublicKey().ToAddress()

    doge_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.DOGECOIN)
    doge_addr = doge_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0).PublicKey().ToAddress()

    return eth_addr, doge_addr


async def get_balance(session: aiohttp.ClientSession, address: str, network: str) -> str:
    url = {
        "eth": f"https://ethbook.guarda.co/api/v2/address/{address}",
        "bnb": f"https://bsc-nn.atomicwallet.io/api/v2/address/{address}",
        "doge": f"https://dogecoin.atomicwallet.io/api/v2/address/{address}"
    }[network]

    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return str(data.get("balance", "0"))
            elif response.status == 429:
                await asyncio.sleep(1)
                return await get_balance(session, address, network)
    except Exception:
        return "0"

    return "0"


total_generated = 0
total_found = 0
total_usd_value = 0
script_start_time = time.time()
batch_counter = 0

async def main():
    global script_start_time, batch_counter, total_generated, total_found, total_usd_value

    clear_console()
    session = await get_shared_session()

    # Change batch_size here to customize how many wallets to process at once, depends on your conditions
    batch_size = 50
    while True:
        batch_data = []
        for _ in range(batch_size):
            total_generated += 1
            mnemonic = Bip39MnemonicGenerator().FromWordsNumber(12) # You can choose this mnemonic between 12 and 24
            seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
            eth_addr, doge_addr = generate_wallet_addresses(seed_bytes)
            batch_data.append((mnemonic, seed_bytes, eth_addr, doge_addr))

        tasks = []
        for mnemonic, seed_bytes, eth_addr, doge_addr in batch_data:
            tasks.extend([
                get_balance(session, eth_addr, "eth"),
                get_balance(session, eth_addr, "bnb"),
                get_balance(session, doge_addr, "doge")
            ])

        results = await asyncio.gather(*tasks, return_exceptions=True)

        result_idx = 0
        for i, (mnemonic, seed_bytes, eth_addr, doge_addr) in enumerate(batch_data):
            eth_bal = results[result_idx] if not isinstance(results[result_idx], Exception) else "0"
            bnb_bal = results[result_idx + 1] if not isinstance(results[result_idx + 1], Exception) else "0"
            doge_bal = results[result_idx + 2] if not isinstance(results[result_idx + 2], Exception) else "0"
            result_idx += 3

            eth_balance = int(eth_bal) / 10**18
            doge_balance = int(doge_bal) / 10**8
            bnb_balance = int(bnb_bal) / 10**18

            found_balance = False

            if eth_balance > 0:
                total_found += 1
                total_usd_value += get_usd_rate(eth_balance, f"https://ethbook.guarda.co/api/v2/tickers/?currency=usd")
                save_found_wallet("Ethereum", eth_addr, eth_balance, mnemonic, seed_bytes.hex())
                found_balance = True

            if doge_balance > 0:
                total_found += 1
                total_usd_value += get_doge_usd_rate(doge_balance)
                save_found_wallet("Dogecoin", doge_addr, doge_balance, mnemonic, seed_bytes.hex())
                found_balance = True

            if bnb_balance > 0:
                total_found += 1
                total_usd_value += get_bnb_usd_rate(bnb_balance)
                save_found_wallet("BNB", eth_addr, bnb_balance, mnemonic, seed_bytes.hex())
                found_balance = True

            if not found_balance and i == batch_size - 1 and batch_counter % 10 == 0:
                elapsed_time = time.time() - script_start_time
                rps = total_generated / elapsed_time if elapsed_time > 0 else 0
                set_terminal_title(f"Gen: {total_generated} / Found: {total_found} / USD: ${total_usd_value} / RPS: {rps:.2f}")

                spacing = " " * 16
                eth_spacing = spacing + " " * (43 - len(eth_addr))
                doge_spacing = spacing + " " * (43 - len(doge_addr))

                print(f"[{total_generated} | Found:{total_found}]  ETH: {CYAN}{eth_addr}{RESET}{eth_spacing}[Balance: {CYAN}{eth_balance}{RESET}]")
                print(f"[{total_generated} | Found:{total_found}]  BNB: {GREEN}{eth_addr}{RESET}{eth_spacing}[Balance: {GREEN}{bnb_balance}{RESET}]")
                print(f"[{total_generated} | Found:{total_found}] DOGE: {YELLOW}{doge_addr}{RESET}{doge_spacing}[Balance: {YELLOW}{doge_balance}{RESET}]")
                print(f"[{total_generated} | Found:{total_found}]  Mne: {RED}{mnemonic}{RESET}")
                print(f"[{total_generated} | Found:{total_found}]  Hex: {seed_bytes.hex()}")
                print("-" * 66)

        batch_counter += 1


# Global shared session for maximum performance, google it if you don't know how to use this functions
shared_connector = None
shared_session = None
semaphore = asyncio.Semaphore(200)  # Limit concurrent requests to avoid overwhelming API

async def get_shared_session():
    global shared_session, shared_connector
    if shared_session is None or shared_session.closed:
        if shared_connector is None:
            shared_connector = aiohttp.TCPConnector(limit=500, limit_per_host=100, ttl_dns_cache=300)
        shared_session = aiohttp.ClientSession(connector=shared_connector)
    return shared_session

async def check_balance_async(address, network):
    # You can use other Crypto if you have a little bit of knowladge
    url = {
        "eth": f"https://ethbook.guarda.co/api/v2/address/{address}",  # Ethereum API
        "bnb": f"https://bsc-nn.atomicwallet.io/api/v2/address/{address}",  # BNB API
        "doge": f"https://dogecoin.atomicwallet.io/api/v2/address/{address}"  # Dogecoin API
    }[network]

    session = await get_shared_session()
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return str(data.get("balance", "0"))
            elif response.status == 429:
                await asyncio.sleep(1)
                return await check_balance_async(address, network)
            else:
                return "0"
    except Exception:
        return "0"

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        elapsed_time = time.time() - script_start_time
        rps = total_generated / elapsed_time if elapsed_time > 0 else 0
        print(f"Final Stats: Generated: {total_generated}, Found: {total_found}, Total USD: ${total_usd_value}, RPS: {rps:.2f}")
        if shared_session and not shared_session.closed:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(shared_session.close())
            loop.close()

