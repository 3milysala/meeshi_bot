# 🚗 MEESHI BOT — Guide de démarrage

## 1. Prérequis

- Python 3.11+ installé sur ton Mac
- Terminal ouvert dans le dossier `meeshi_bot`

---

## 2. Installation

```bash
# Crée un environnement virtuel (recommandé)
python3 -m venv venv
source venv/bin/activate

# Installe les dépendances
pip install -r requirements.txt
```

---

## 3. Configuration — AVANT de lancer

Ouvre `config.py` et renseigne :

### ADMIN_CHANNEL_ID
C'est l'ID de ton channel Telegram privé où tu recevras les commandes.
Pour le trouver :
1. Ajoute @userinfobot dans ton channel
2. Il t'enverra l'ID (commence par -100...)
OU
1. Va sur https://api.telegram.org/bot<TON_TOKEN>/getUpdates
2. Cherche "chat":{"id": -100XXXXXXXXX dans les résultats

Remplace `None` par ton ID :
```python
ADMIN_CHANNEL_ID = -1001234567890  # ton vrai ID ici
```

---

## 4. Lancer le bot

```bash
# Assure-toi d'être dans le venv
source venv/bin/activate

# Lance
python bot.py
```

Le bot tourne tant que le terminal est ouvert.
Pour le garder actif en arrière-plan :
```bash
nohup python bot.py &
```

---

## 5. Ajouter des articles au catalogue

Dans `config.py`, ajoute des entrées dans `CATALOG` :

```python
{
    "id":          "nom_unique_sans_espaces",
    "name":        "Nom affiché",
    "unit":        "ghoul",
    "price_eur":   25.0,
    "stock":       5,
    "description": "Description courte",
    "emoji":       "🚗",
},
```

---

## 6. Ajouter XMR plus tard

Dans `config.py` :
```python
WALLETS = {
    ...
    "XMR": "ton_adresse_xmr",
}

PAYMENT_LABELS = {
    ...
    "XMR": "Monero (XMR)",
}
```

Dans `prices.py`, décommente les lignes XMR.

---

## 7. Flux d'une commande

```
Client /start
  → Voit le catalogue + stock
  → Choisit l'article
  → Choisit la quantité (ghouls)
  → Choisit la crypto
  → Reçoit l'adresse wallet + montant exact converti
  → Clique "J'ai payé"
  → Entre son adresse de livraison (nom, rue, ville, pays, CP)
  → Confirmation affichée

Toi :
  → Tu reçois la notif dans ton channel avec TOUT
  → Tu vérifies le paiement sur l'explorer blockchain
  → Tu confirmes au client et tu envoies le colis
```

---

## 8. Vérifier les paiements manuellement

- **BTC** : https://mempool.space/address/bc1qgh490ulvuq6se23sdv5qlwwdt85ecys6lh2r36
- **USDT/USDC SOL** : https://solscan.io/account/FQ9SxMu3pRDYENoNL95vAdikS8KgwWVPJDqU6sKLjwP8
