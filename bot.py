#!/usr/bin/env python3
"""
MEESHI BOT
Bot Telegram de vente de Hot Wheels de collection.
"""

import logging
import asyncio
import uuid
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode

from config import BOT_TOKEN, ADMIN_CHANNEL_ID, WALLETS, PAYMENT_LABELS, CATALOG, MAX_QUANTITY
from prices import get_crypto_price

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── États de la conversation ──────────────────────────────────────────────────
(
    STATE_CATALOG,
    STATE_QUANTITY,
    STATE_PAYMENT,
    STATE_AWAITING_PAYMENT,
    STATE_ADDRESS_NAME,
    STATE_ADDRESS_STREET,
    STATE_ADDRESS_CITY,
    STATE_ADDRESS_COUNTRY,
    STATE_ADDRESS_ZIP,
) = range(9)


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_item_by_id(item_id: str):
    for item in CATALOG:
        if item["id"] == item_id:
            return item
    return None

def in_stock(item: dict) -> bool:
    return item["stock"] > 0

def order_id() -> str:
    return str(uuid.uuid4())[:8].upper()

def now_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")


# ── /start ────────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()

    lines = [
        "👋 *Bienvenue sur MEESHI SHOP*",
        "",
        "Ici tu peux acheter des Hot Wheels de collection — appelées *Meeshis*.",
        "Chaque voiture est une *ghoul* 👻",
        "",
        "📦 *Stock disponible :*",
    ]

    keyboard = []
    for item in CATALOG:
        stock_txt = f"{item['stock']} ghouls" if item["stock"] > 0 else "❌ Épuisé"
        lines.append(
            f"\n🚗 *{item['name']}*\n"
            f"   {item['description']}\n"
            f"   💶 {item['price_eur']}€ / ghoul  |  📦 Stock : {stock_txt}"
        )
        if in_stock(item):
            keyboard.append([
                InlineKeyboardButton(
                    f"🛒 Commander {item['name']}",
                    callback_data=f"select_{item['id']}"
                )
            ])

    if not keyboard:
        lines.append("\n_Aucun article en stock pour l'instant. Reviens bientôt !_")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
    )
    return STATE_CATALOG


# ── Sélection article ─────────────────────────────────────────────────────────

async def select_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    item_id = query.data.replace("select_", "")
    item = get_item_by_id(item_id)
    if not item or not in_stock(item):
        await query.edit_message_text("❌ Cet article n'est plus disponible.")
        return ConversationHandler.END

    context.user_data["item"] = item

    max_q = min(MAX_QUANTITY, item["stock"])
    buttons = []
    row = []
    for i in range(1, max_q + 1):
        row.append(InlineKeyboardButton(str(i), callback_data=f"qty_{i}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("❌ Annuler", callback_data="cancel")])

    await query.edit_message_text(
        f"🚗 *{item['name']}*\n"
        f"{item['description']}\n\n"
        f"💶 *{item['price_eur']}€* par ghoul\n\n"
        f"Combien de ghouls tu veux ? (max {max_q})",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return STATE_QUANTITY


# ── Choix quantité ────────────────────────────────────────────────────────────

async def select_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    qty = int(query.data.replace("qty_", ""))
    item = context.user_data["item"]
    total_eur = round(item["price_eur"] * qty, 2)

    context.user_data["quantity"] = qty
    context.user_data["total_eur"] = total_eur

    # Boutons de paiement
    buttons = []
    for key, label in PAYMENT_LABELS.items():
        buttons.append([InlineKeyboardButton(label, callback_data=f"pay_{key}")])
    buttons.append([InlineKeyboardButton("❌ Annuler", callback_data="cancel")])

    await query.edit_message_text(
        f"🛒 *Récap de ta commande :*\n\n"
        f"🚗 {item['name']} × {qty} ghoul{'s' if qty > 1 else ''}\n"
        f"💶 Total : *{total_eur}€*\n\n"
        f"Choisis ton moyen de paiement 👇",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return STATE_PAYMENT


# ── Choix paiement ────────────────────────────────────────────────────────────

async def select_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    crypto_key = query.data.replace("pay_", "")
    item = context.user_data["item"]
    total_eur = context.user_data["total_eur"]
    qty = context.user_data["quantity"]

    context.user_data["crypto"] = crypto_key
    oid = order_id()
    context.user_data["order_id"] = oid

    # Conversion EUR → crypto
    await query.edit_message_text("⏳ Récupération du taux de change en cours...")

    crypto_amount, rate_info = await get_crypto_price(crypto_key, total_eur)

    if crypto_amount is None:
        await query.edit_message_text(
            "❌ Impossible de récupérer le taux de change. Réessaie dans quelques instants.\n"
            "Tape /start pour recommencer."
        )
        return ConversationHandler.END

    context.user_data["crypto_amount"] = crypto_amount
    wallet = WALLETS[crypto_key]
    label = PAYMENT_LABELS[crypto_key]

    context.user_data["wallet"] = wallet

    confirm_btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ J'ai payé", callback_data="paid")],
        [InlineKeyboardButton("❌ Annuler", callback_data="cancel")],
    ])

    await query.edit_message_text(
        f"💳 *Paiement — Commande #{oid}*\n\n"
        f"🚗 {item['name']} × {qty} ghoul{'s' if qty > 1 else ''}\n"
        f"💶 {total_eur}€  →  *{crypto_amount} {crypto_key.split('_')[0]}*\n"
        f"_{rate_info}_\n\n"
        f"📤 Envoie exactement ce montant à :\n"
        f"`{wallet}`\n\n"
        f"⚠️ *Réseau :* {'Solana (SPL)' if 'SOL' in crypto_key else 'Bitcoin mainnet'}\n\n"
        f"Une fois le paiement envoyé, clique sur *J'ai payé* 👇",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=confirm_btn,
    )
    return STATE_AWAITING_PAYMENT


# ── Confirmation paiement ─────────────────────────────────────────────────────

async def payment_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "✅ Super ! Maintenant j'ai besoin de ton adresse de livraison.\n\n"
        "Commence par ton *prénom et nom* :",
        parse_mode=ParseMode.MARKDOWN,
    )
    return STATE_ADDRESS_NAME


# ── Collecte adresse ──────────────────────────────────────────────────────────

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["addr_name"] = update.message.text.strip()
    await update.message.reply_text("🏠 *Rue et numéro* :", parse_mode=ParseMode.MARKDOWN)
    return STATE_ADDRESS_STREET

async def get_street(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["addr_street"] = update.message.text.strip()
    await update.message.reply_text("🏙️ *Ville* :", parse_mode=ParseMode.MARKDOWN)
    return STATE_ADDRESS_CITY

async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["addr_city"] = update.message.text.strip()
    await update.message.reply_text("🌍 *Pays* :", parse_mode=ParseMode.MARKDOWN)
    return STATE_ADDRESS_COUNTRY

async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["addr_country"] = update.message.text.strip()
    await update.message.reply_text("📮 *Code postal* :", parse_mode=ParseMode.MARKDOWN)
    return STATE_ADDRESS_ZIP

async def get_zip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["addr_zip"] = update.message.text.strip()
    return await finalize_order(update, context)


# ── Finalisation commande ─────────────────────────────────────────────────────

async def finalize_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    d = context.user_data
    user = update.effective_user
    item = d["item"]
    qty = d["quantity"]
    oid = d["order_id"]
    crypto_key = d["crypto"]
    crypto_amount = d["crypto_amount"]
    wallet = d["wallet"]
    label = PAYMENT_LABELS[crypto_key]

    # Message client
    await update.message.reply_text(
        f"🎉 *Commande #{oid} enregistrée !*\n\n"
        f"🚗 {item['name']} × {qty} ghoul{'s' if qty > 1 else ''}\n"
        f"💳 Paiement : {crypto_amount} {crypto_key.split('_')[0]} ({label})\n"
        f"📦 Adresse : {d['addr_street']}, {d['addr_zip']} {d['addr_city']}, {d['addr_country']}\n\n"
        f"Je vais vérifier ton paiement et je te contacte dès que c'est confirmé. 👌\n\n"
        f"_En cas de souci, contacte-moi directement._",
        parse_mode=ParseMode.MARKDOWN,
    )

    # Mise à jour stock
    item["stock"] -= qty

    # Notification admin
    if ADMIN_CHANNEL_ID:
        username = f"@{user.username}" if user.username else f"ID:{user.id}"
        admin_msg = (
            f"🛍️ *NOUVELLE COMMANDE #{oid}*\n"
            f"📅 {now_str()}\n\n"
            f"👤 Client : {username} (ID: `{user.id}`)\n"
            f"🚗 Article : {item['name']} × {qty} ghoul{'s' if qty > 1 else ''}\n"
            f"💶 Total : {d['total_eur']}€\n"
            f"💳 Crypto : `{crypto_amount} {crypto_key.split('_')[0]}` ({label})\n"
            f"📤 Wallet utilisé : `{wallet}`\n\n"
            f"📦 *ADRESSE DE LIVRAISON :*\n"
            f"   {d['addr_name']}\n"
            f"   {d['addr_street']}\n"
            f"   {d['addr_zip']} {d['addr_city']}\n"
            f"   {d['addr_country']}\n\n"
            f"⚠️ *À VÉRIFIER :* paiement de `{crypto_amount} {crypto_key.split('_')[0]}` sur `{wallet}`"
        )
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHANNEL_ID,
                text=admin_msg,
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            logger.error(f"Erreur envoi admin channel: {e}")

    return ConversationHandler.END


# ── Annulation ────────────────────────────────────────────────────────────────

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("❌ Commande annulée. Tape /start pour recommencer.")
    else:
        await update.message.reply_text(
            "❌ Commande annulée. Tape /start pour recommencer.",
            reply_markup=ReplyKeyboardRemove(),
        )
    context.user_data.clear()
    return ConversationHandler.END


# ── Fallback texte inattendu ──────────────────────────────────────────────────

async def unexpected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Utilise /start pour commencer une commande. 🛒"
    )


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    if not ADMIN_CHANNEL_ID:
        logger.warning("⚠️  ADMIN_CHANNEL_ID non configuré dans config.py — les notifications admin ne seront pas envoyées.")

    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STATE_CATALOG: [
                CallbackQueryHandler(select_item, pattern=r"^select_"),
                CallbackQueryHandler(cancel, pattern=r"^cancel$"),
            ],
            STATE_QUANTITY: [
                CallbackQueryHandler(select_quantity, pattern=r"^qty_"),
                CallbackQueryHandler(cancel, pattern=r"^cancel$"),
            ],
            STATE_PAYMENT: [
                CallbackQueryHandler(select_payment, pattern=r"^pay_"),
                CallbackQueryHandler(cancel, pattern=r"^cancel$"),
            ],
            STATE_AWAITING_PAYMENT: [
                CallbackQueryHandler(payment_confirmed, pattern=r"^paid$"),
                CallbackQueryHandler(cancel, pattern=r"^cancel$"),
            ],
            STATE_ADDRESS_NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            STATE_ADDRESS_STREET:  [MessageHandler(filters.TEXT & ~filters.COMMAND, get_street)],
            STATE_ADDRESS_CITY:    [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            STATE_ADDRESS_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
            STATE_ADDRESS_ZIP:     [MessageHandler(filters.TEXT & ~filters.COMMAND, get_zip)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unexpected))

    logger.info("🚗 Meeshi Bot démarré !")
    await app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
