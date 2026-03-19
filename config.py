# ============================================================
#  MEESHI BOT — CONFIG
#  Modifie ce fichier pour mettre à jour tes infos
# ============================================================

# --- TOKEN BOT TELEGRAM ---
BOT_TOKEN = "8453652179:AAFMKwD1flzJB27ur0YoSqYHeuIaTIoN2IM"

# --- CANAL DE NOTIFICATIONS (remplace par ton ID) ---
# Format : -100XXXXXXXXXX
ADMIN_CHANNEL_ID = -1003899399643

# --- WALLETS ---
WALLETS = {
    "BTC":      "bc1qgh490ulvuq6se23sdv5qlwwdt85ecys6lh2r36",
    "USDT_SOL": "FQ9SxMu3pRDYENoNL95vAdikS8KgwWVPJDqU6sKLjwP8",
    "USDC_SOL": "FQ9SxMu3pRDYENoNL95vAdikS8KgwWVPJDqU6sKLjwP8",
    # "XMR":    "ton_adresse_xmr_ici",  # décommenter quand dispo
}

PAYMENT_LABELS = {
    "BTC":      "Bitcoin (BTC)",
    "USDT_SOL": "USDT sur Solana",
    "USDC_SOL": "USDC sur Solana",
}

# --- CATALOGUE ---
# stock = nombre de ghouls disponibles
CATALOG = [
    {
        "id":          "agartha1g",
        "name":        "Meeshi Agartha",
        "unit":        "ghoul",
        "price_eur":   15.0,
        "stock":       20,
        "description": "Édition Mexicaine, exportation directe vers Agartha et la Terre Intérieure 🌀",
        "emoji":       "🚗",
    },
]

# --- LIMITES ---
MAX_QUANTITY = 10   # max ghouls par commande
