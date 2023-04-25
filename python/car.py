import os
import psycopg2
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

chat_table_choice = {}


def add_data_to_database(table_name, id, date, payout, availability, payout_type=""):
    try:
        conn = psycopg2.connect(database="postgres", user="postgres", password="Yliana72", host="localhost",
                                port="5432")
        cursor = conn.cursor()

        # if table_name == "aggr_order":
        #     insert_query = f"INSERT INTO aggr_order (id, date, payout, payout_type, availability) VALUES ({id}, '{date}', {payout}, '{payout_type}', {availability});"
        # elif table_name == "friend_order":
        #     insert_query = f"INSERT INTO friend_order (id, date, payout, availability) VALUES ({id}, '{date}', {payout}, {availability});"
        # else:
        #     raise ValueError("Invalid table name")

        current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if table_name == "aggr_order":
            insert_query = f"INSERT INTO aggr_order (id, date, payout, payout_type, availability, timestamp) VALUES ({id}, '{date}', {payout}, '{payout_type}', {availability}, '{current_timestamp}');"
        elif table_name == "friend_order":
            insert_query = f"INSERT INTO friend_order (id, date, payout, availability, timestamp) VALUES ({id}, '{date}', {payout}, {availability}, '{current_timestamp}');"

        cursor.execute(insert_query)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(str(e))


def handle_table_selection(update: Update, context: CallbackContext, table_choice):
    if table_choice == "aggr_order" or table_choice == "friend_order":
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"Please send me the data to insert into the {table_choice} table.")
        chat_table_choice[update.effective_chat.id] = table_choice
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Invalid table name. Please choose either 'aggr_order' or 'friend_order'.")


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
        [InlineKeyboardButton("Агрегатор", callback_data="aggr_order"),
         InlineKeyboardButton("Дружеский заказ", callback_data="friend_order")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Please select the table you want to insert data into:", reply_markup=reply_markup)


def start(update: Update, context: CallbackContext):
    instructions = '''
    Добро пожаловать в наш бот для отслеживания заказов эвакуатора!
    
    Инструкция по использованию бота:
    1. Напишите команду /start, чтобы начать работу с ботом.
    2. Выберите таблицу, в которую хотите добавить данные, нажав на одну из кнопок: "Заказ через агрегатор или с улицы" или "Дружеский заказ".
    3. Введите данные заказа, следуя формату, указанному ниже:
       - Для таблицы "Агрегатор": ID(Александр - 1, Борис - 2),Дата,Сумма,Тип выплаты,Доступность (например: 1,2023-04-23,5000,cash,True)
       - Для таблицы "Дружеский": ID(Александр - 1, Борис - 2),Дата,Сумма,Доступность (например: 2,2023-04-23,3500,True)
    4. Используйте команду /end_day, чтобы завершить день и рассчитать зарплаты и обновить данные в таблице банка. Вы можете добавить аргумент "today" или "yesterday" для расчета зарплат и обновления банка за текущий или предыдущий день (например: /end_day today). Вы также можете указать день, для которого нужно рассчитать зарплату, добавив аргумент 'today' или 'yesterday'. Например: /end_day today или /end_day yesterday.
    '''

    context.bot.send_message(chat_id=update.effective_chat.id, text=instructions)
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
    day = 'today'
    if context.args and context.args[0] in ['today', 'yesterday']:
        day = context.args[0]

    try:
        conn = psycopg2.connect(database="postgres", user="postgres", password="Yliana72", host="localhost",
                                port="5432")
        cursor = conn.cursor()

        # Get the date based on the day parameter
        if day == 'today':
            target_date = datetime.datetime.now()
        else:
            target_date = datetime.datetime.now() - datetime.timedelta(days=1)

        target_date_str = target_date.strftime('%Y-%m-%d')

        # Calculate cash, air sums, and salary for each id
        for id in [1, 2]:
            cursor.execute(
                f"SELECT SUM(payout) FROM aggr_order WHERE id = {id} AND date = '{target_date_str}' AND payout_type = 'cash';")
            cash_sum = cursor.fetchone()[0] or 0

            cursor.execute(
                f"SELECT SUM(payout) FROM aggr_order WHERE id = {id} AND date = '{target_date_str}' AND payout_type = 'air';")
            air_sum = cursor.fetchone()[0] or 0

            cursor.execute(f"SELECT SUM(payout) FROM friend_order WHERE id = {id} AND date = '{target_date_str}';")
            friend_payout_sum = cursor.fetchone()[0] or 0

            total_cash = cash_sum + friend_payout_sum
            total_air = air_sum

            cursor.execute(f"SELECT COUNT(*) FROM aggr_order WHERE id = {id} AND date = '{target_date_str}';")
            aggr_order_count = cursor.fetchone()[0] or 0

            cursor.execute(f"SELECT COUNT(*) FROM friend_order WHERE id = {id} AND date = '{target_date_str}';")
            friend_order_count = cursor.fetchone()[0] or 0

            total_record_count = aggr_order_count + friend_order_count

            cursor.execute(
                f"SELECT payout FROM aggr_order WHERE id = {id} AND date = '{target_date_str}' AND payout_type = 'cash' ORDER BY timestamp DESC;")
            aggr_cash_payouts = [row[0] for row in cursor.fetchall()]

            cursor.execute(
                f"SELECT payout FROM aggr_order WHERE id = {id} AND date = '{target_date_str}' AND payout_type = 'air' ORDER BY timestamp DESC;")
            aggr_air_payouts = [row[0] for row in cursor.fetchall()]

            cursor.execute(
                f"SELECT payout FROM friend_order WHERE id = {id} AND date = '{target_date_str}' ORDER BY timestamp DESC;")
            friend_payouts = [row[0] for row in cursor.fetchall()]

            all_payouts = sorted(aggr_cash_payouts + aggr_air_payouts + friend_payouts, reverse=True)
            sum_after_first_3 = sum(all_payouts[3:])

            sum_after_first_3_excluding_first_3 = 0

            base_salary = 2500
            record_limit = 12000
            if (total_cash + total_air) > record_limit:
                salary = base_salary + 0.5 * (total_cash + total_air - record_limit)
            elif total_record_count > 3:
                # Calculate sum of payouts after the first 3 records
                cursor.execute(f"""
                    SELECT SUM(payout) FROM (
                        SELECT payout FROM (
                            SELECT payout, timestamp FROM aggr_order WHERE id = {id} AND date = '{target_date_str}'
                            UNION ALL
                            SELECT payout, timestamp FROM friend_order WHERE id = {id} AND date = '{target_date_str}'
                        ) AS all_orders
                        ORDER BY timestamp ASC
                        OFFSET 3
                    ) AS payouts_after_first_3;
                    """)
                sum_after_first_3_excluding_first_3 = cursor.fetchone()[0] or 0

                salary = base_salary + 0.5 * sum_after_first_3_excluding_first_3
            elif total_record_count > 0:
                salary = base_salary
            else:
                salary = 0

            if (total_cash + total_air > record_limit) and (total_record_count > 3):
                cursor.execute(f"""
                    SELECT SUM(payout) FROM (
                        SELECT payout FROM (
                            SELECT payout, timestamp FROM aggr_order WHERE id = {id} AND date = '{target_date_str}'
                            UNION ALL
                            SELECT payout, timestamp FROM friend_order WHERE id = {id} AND date = '{target_date_str}'
                        ) AS all_orders
                        ORDER BY timestamp ASC
                        OFFSET 3
                    ) AS payouts_after_first_3;
                    """)
                sum_after_first_3_excluding_first_3 = cursor.fetchone()[0] or 0
                if (base_salary + 0.5 * (total_cash + total_air - record_limit)) > (
                        base_salary + 0.5 * sum_after_first_3_excluding_first_3):
                    salary = base_salary + 0.5 * (total_cash + total_air - record_limit)
                else:
                    salary = base_salary + 0.5 * sum_after_first_3_excluding_first_3

            insert_query = f"""
            INSERT INTO salary (id, date, cash, air, salary)
            VALUES ({id}, '{target_date_str}', {total_cash}, {total_air}, {salary})
            ON CONFLICT (id, date)
            DO UPDATE SET cash = {total_cash}, air = {total_air}, salary = {salary};
            """
            cursor.execute(insert_query)

            # Calculate the sum of all salaries for the day
            cursor.execute(f"SELECT SUM(salary) FROM salary WHERE date = '{target_date_str}';")
            total_salary = cursor.fetchone()[0] or 0

            # Calculate the sum of all cash and air for the day
            cursor.execute(f"SELECT SUM(cash) + SUM(air) FROM salary WHERE date = '{target_date_str}';")
            total_cash_and_air = cursor.fetchone()[0] or 0

            # Get the previous day's amount from the bank table
            prev_day = target_date - datetime.timedelta(days=1)
            prev_day_str = prev_day.strftime('%Y-%m-%d')
            cursor.execute(f"SELECT amount FROM bank WHERE date = '{prev_day_str}';")
            prev_day_amount = cursor.fetchone()

            if prev_day_amount:
                prev_day_amount = prev_day_amount[0]
            else:
                prev_day_amount = 0

            # Calculate the new amount for the present day
            new_amount = prev_day_amount - total_salary + total_cash_and_air

            # Insert or update the bank table for the present day
            insert_query = f"""
            INSERT INTO bank (date, amount)
            VALUES ('{target_date_str}', {new_amount})
            ON CONFLICT (date)
            DO UPDATE SET amount = {new_amount};
            """
            cursor.execute(insert_query)

            if id == 1:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"💰 Зарплата Александра {salary}")
            else:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"💰 Зарплата Бориса {salary}")

        conn.commit()
        cursor.close()
        conn.close()
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"End of {day} data added to the salary table and updated the bank table.")
    except Exception as e:
        print(str(e))
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Error occurred while processing end of day data.")


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