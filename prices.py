"""
Conversion EUR → crypto via CoinGecko (API publique, sans clé, sans compte).
"""

import aiohttp
import logging

logger = logging.getLogger(__name__)

# CoinGecko IDs
COINGECKO_IDS = {
    "BTC":      "bitcoin",
    "USDT_SOL": "tether",
    "USDC_SOL": "usd-coin",
    # "XMR":    "monero",
}

# Nombre de décimales à afficher par crypto
DECIMALS = {
    "BTC":      6,
    "USDT_SOL": 2,
    "USDC_SOL": 2,
    # "XMR":    4,
}


async def get_crypto_price(crypto_key: str, amount_eur: float):
    """
    Retourne (montant_crypto, info_taux) ou (None, message_erreur).
    """
    cg_id = COINGECKO_IDS.get(crypto_key)
    if not cg_id:
        return None, "Crypto non supportée"

    url = (
        f"https://api.coingecko.com/api/v3/simple/price"
        f"?ids={cg_id}&vs_currencies=eur"
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return None, f"Erreur API ({resp.status})"
                data = await resp.json()

        price_eur = data[cg_id]["eur"]
        crypto_amount = round(amount_eur / price_eur, DECIMALS[crypto_key])
        rate_info = f"1 {crypto_key.split('_')[0]} = {price_eur:,.2f}€ (CoinGecko)"
        return crypto_amount, rate_info

    except Exception as e:
        logger.error(f"Erreur CoinGecko: {e}")
        return None, str(e)
