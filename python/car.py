import os
import psycopg2
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

chat_table_choice = {}

def add_data_to_database(table_name, id, date, payout, availability, payout_type=""):
    try:
        conn = psycopg2.connect(database="postgres", user="postgres", password="Yliana72", host="localhost", port="5432")
        cursor = conn.cursor()

        if table_name == "aggr_order":
            insert_query = f"INSERT INTO aggr_order (id, date, payout, payout_type, availability) VALUES ({id}, '{date}', {payout}, '{payout_type}', {availability});"
        elif table_name == "friend_order":
            insert_query = f"INSERT INTO friend_order (id, date, payout, availability) VALUES ({id}, '{date}', {payout}, {availability});"
        else:
            raise ValueError("Invalid table name")

        cursor.execute(insert_query)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(str(e))

def handle_table_selection(update: Update, context: CallbackContext, table_choice):
    if table_choice == "aggr_order" or table_choice == "friend_order":
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"Please send me the data to insert into the {table_choice} table.")
        chat_table_choice[update.effective_chat.id] = table_choice
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid table name. Please choose either 'aggr_order' or 'friend_order'.")

def parse_and_process_aggr_order_data(message_text, chat_id, context):
    tokens = message_text.split(',')

    id = int(tokens[0])
    date = tokens[1]
    payout = float(tokens[2]) * 0.85
    payout_type = tokens[3]
    availability = tokens[4].lower() in ["true", "1"]

    add_data_to_database("aggr_order", id, date, payout, availability, payout_type)
    context.bot.send_message(chat_id=chat_id, text="Data added to the aggr_order table.")

def parse_and_process_friend_order_data(message_text, chat_id, context):
    tokens = message_text.split(',')

    id = int(tokens[0])
    date = tokens[1]
    payout = float(tokens[2])
    availability = tokens[3].lower() in ["true", "1"]

    add_data_to_database("friend_order", id, date, payout, availability)
    context.bot.send_message(chat_id=chat_id, text="Data added to the friend_order table.")

def send_table_selection_buttons(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("aggr_order", callback_data="aggr_order"),
         InlineKeyboardButton("friend_order", callback_data="friend_order")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(chat_id=update.effective_chat.id, text="Please select the table you want to insert data into:", reply_markup=reply_markup)

def start(update: Update, context: CallbackContext):
    send_table_selection_buttons(update, context)

def handle_callback_query(update: Update, context: CallbackContext):
    query = update.callback_query
    table_choice = query.data
    handle_table_selection(update, context, table_choice)

def handle_message(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    table_choice = chat_table_choice.get(chat_id)

    if table_choice:
        if table_choice == "aggr_order":
            parse_and_process_aggr_order_data(update.message.text, chat_id, context)
        elif table_choice == "friend_order":
            parse_and_process_friend_order_data(update.message.text, chat_id, context)
        del chat_table_choice[chat_id]
    else:
        context.bot.send_message(chat_id=chat_id, text="Please select a table first using the /start command.")

def end_day(update: Update, context: CallbackContext):
    try:
        conn = psycopg2.connect(database="postgres", user="postgres", password="Yliana72", host="localhost", port="5432")
        cursor = conn.cursor()

        # Get the current date
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')

        # Calculate cash and air sums for each id
        for id in [1, 2]:
            cursor.execute(f"SELECT SUM(payout) FROM aggr_order WHERE id = {id} AND date = '{current_date}' AND payout_type = 'cash';")
            cash_sum = cursor.fetchone()[0] or 0

            cursor.execute(f"SELECT SUM(payout) FROM aggr_order WHERE id = {id} AND date = '{current_date}' AND payout_type = 'air';")
            air_sum = cursor.fetchone()[0] or 0

            cursor.execute(f"SELECT SUM(payout) FROM friend_order WHERE id = {id} AND date = '{current_date}';")
            friend_payout_sum = cursor.fetchone()[0] or 0

            total_cash = cash_sum + friend_payout_sum
            total_air = air_sum

            # Insert or update the cash and air sums in the salary table
            insert_query = f"""
            INSERT INTO salary (id, date, cash, air)
            VALUES ({id}, '{current_date}', {total_cash}, {total_air})
            ON CONFLICT (id, date)
            DO UPDATE SET cash = {total_cash}, air = {total_air};
            """
            cursor.execute(insert_query)

        conn.commit()
        cursor.close()
        conn.close()
        context.bot.send_message(chat_id=update.effective_chat.id, text="End of day data added to the salary table.")
    except Exception as e:
        print(str(e))
        context.bot.send_message(chat_id=update.effective_chat.id, text="Error occurred while processing end of day data.")


def main():
    token = "5600063503:AAHPtxvBH3w0MBqoHTEaDtUjRLX7lNMKXxE"
    updater = Updater(token, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(handle_callback_query))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CommandHandler("end_day", end_day))
    print("Bot started")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

