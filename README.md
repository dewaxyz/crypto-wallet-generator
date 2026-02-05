# Crypto Wallet Generator

Python script that generates BIP39 mnemonics and checks balances across Ethereum, Dogecoin, and BNB networks.

## Features

- Generates random 12-word BIP39 mnemonics
- Derives addresses using BIP44 standard
- High-performance concurrent balance checking with asyncio
- Optimized connection pooling (500 total, 100 per host)
- Real-time statistics and progress display
- Automatic saving of found wallets
- Intelligent rate limit handling with retry logic
- Configurable batch processing for performance tuning

## Requirements

- Python 3.8+
- Dependencies in requirements.txt

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python crypto.py
```

The script will continuously generate wallets and check balances. Found wallets are saved to `found_wallets/` directory.

## Configuration

Modify `batch_size` in crypto.py to adjust performance:
- Lower values (10-25): More responsive, lower RPS
- Higher values (50-100): Higher RPS, more memory usage

## Output

- Terminal title shows: `Gen: X / Found: Y / USD: $Z / RPS: W`
- Sample wallets displayed every 10 batches
- Found wallets saved with mnemonic, addresses, and balances

## Performance

- 50 wallets per batch (150 API calls)
- Optimized connection pooling
- Typical: 15-25 RPS

## Networks

- Ethereum (Guarda API)
- Dogecoin (Atomic Wallet API)
- BNB Smart Chain (Atomic Wallet API)

## Disclaimer

For educational purposes only. Generating random wallets may occasionally find existing balances, but this is extremely rare. Use at your own risk.

## Author

XieyeT
