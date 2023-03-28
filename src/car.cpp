#include <iostream>
#include <sstream>
#include <string>
#include <tgbot/tgbot.h>
#include <pqxx/pqxx>
#include <unordered_map>

std::unordered_map<int64_t, std::string> chat_table_choice;

void addDataToDatabase(const std::string& table_name, int id, std::string date, double payout, bool availability, const std::string& payout_type = "") {
    try {
        pqxx::connection conn("dbname=mydatabase user=postgres password=761142 host=localhost port=5432");
        pqxx::work txn(conn);

        std::string insert_query;

        if (table_name == "aggr_order") {
            insert_query = "INSERT INTO aggr_order (id, date, payout, payout_type, availability) VALUES (" +
                           std::to_string(id) + ", '" + date + "', " + std::to_string(payout) + ", '" +
                           payout_type + "', " + (availability ? "TRUE" : "FALSE") + ");";
        } else if (table_name == "friend_order") {
            insert_query = "INSERT INTO friend_order (id, date, payout, availability) VALUES (" +
                           std::to_string(id) + ", '" + date + "', " + std::to_string(payout) + ", " +
                           (availability ? "TRUE" : "FALSE") + ");";
        } else {
            throw std::runtime_error("Invalid table name");
        }

        txn.exec(insert_query);
        txn.commit();
    } catch (const std::exception &e) {
        std::cerr << e.what() << std::endl;
    }
}

void handleTableSelection(TgBot::Message::Ptr message, const std::string& table_choice, const TgBot::Bot& bot) {
    if (table_choice == "aggr_order" || table_choice == "friend_order") {
        bot.getApi().sendMessage(message->chat->id, "Please send me the data to insert into the " + table_choice + " table.");
        chat_table_choice[message->chat->id] = table_choice;
    } else {
        bot.getApi().sendMessage(message->chat->id, "Invalid table name. Please choose either 'aggr_order' or 'friend_order'.");
    }
}

void parseAndProcessAggrOrderData(const std::string& message_text, int chat_id, const TgBot::Bot& bot) {
    std::stringstream ss(message_text);
    std::string token;

    getline(ss, token, ',');
    int id = std::stoi(token);

    getline(ss, token, ',');
    std::string date = token;

    getline(ss, token, ',');
    double payout = std::stod(token) * 0.85;

    getline(ss, token, ',');
    std::string payout_type = token;

    getline(ss, token, ',');
    bool availability = (token == "true" || token == "1");

    // Insert data into the aggr_order table
    addDataToDatabase("aggr_order", id, date, payout, availability, payout_type);
    bot.getApi().sendMessage(chat_id, "Data added to the aggr_order table.");
}

void parseAndProcessFriendOrderData(const std::string& message_text, int chat_id, const TgBot::Bot& bot) {
    std::stringstream ss(message_text);
    std::string token;

    getline(ss, token, ',');
    int id = std::stoi(token);

    getline(ss, token, ',');
    std::string date = token;

    getline(ss, token, ',');
    double payout = std::stod(token);

    getline(ss, token, ',');
    bool availability = (token == "true" || token == "1");

    // Insert data into the friend_order table
    addDataToDatabase("friend_order", id, date, payout, availability);
    bot.getApi().sendMessage(chat_id, "Data added to the friend_order table.");
}

void sendTableSelectionButtons(int64_t chat_id, const TgBot::Bot& bot) {
    TgBot::InlineKeyboardMarkup::Ptr markup(new TgBot::InlineKeyboardMarkup);
    TgBot::InlineKeyboardButton::Ptr buttonAggrOrder(new TgBot::InlineKeyboardButton);
    buttonAggrOrder->text = "aggr_order";
    buttonAggrOrder->callbackData = "aggr_order";

    TgBot::InlineKeyboardButton::Ptr buttonFriendOrder(new TgBot::InlineKeyboardButton);
    buttonFriendOrder->text = "friend_order";
    buttonFriendOrder->callbackData = "friend_order";

    std::vector<TgBot::InlineKeyboardButton::Ptr> row;
    row.push_back(buttonAggrOrder);
    row.push_back(buttonFriendOrder);
    markup->inlineKeyboard.push_back(row);

    bot.getApi().sendMessage(chat_id, "Please select the table you want to insert data into:", false, 0, markup);
}

int main() {
    std::string token = "5600063503:AAHPtxvBH3w0MBqoHTEaDtUjRLX7lNMKXxE";
    TgBot::Bot bot(token);

    bot.getEvents().onCommand("start", [&bot](TgBot::Message::Ptr message) {
        sendTableSelectionButtons(message->chat->id, bot);
    });

    bot.getEvents().onCallbackQuery([&bot](TgBot::CallbackQuery::Ptr query) {
        if (query->data == "aggr_order" || query->data == "friend_order") {
            handleTableSelection(query->message, query->data, bot);
        }
    });

    bot.getEvents().onAnyMessage([&bot](TgBot::Message::Ptr message) {
        if (message->text.find("/") == 0) {
            // Ignore command messages (e.g., "/start")
            return;
        }

        int64_t chat_id = message->chat->id;
        auto table_choice_it = chat_table_choice.find(chat_id);

        if (table_choice_it != chat_table_choice.end()) {
            std::string table_choice = table_choice_it->second;
            if (table_choice == "aggr_order") {
                parseAndProcessAggrOrderData(message->text, chat_id, bot);
            } else if (table_choice == "friend_order") {
                parseAndProcessFriendOrderData(message->text, chat_id, bot);
            }
            chat_table_choice.erase(chat_id);  // Remove the table choice after processing the data
        } else {
            bot.getApi().sendMessage(chat_id, "Please select a table first using the /start command.");
        }
    });

    try {
        printf("Bot username: %s\n", bot.getApi().getMe()->username.c_str());
//        bot.getApi().sendMessage(message->chat->id, "Hello World");
        TgBot::TgLongPoll longPoll(bot);
        while (true) {
            printf("Long poll started\n");
            longPoll.start();
        }
    } catch (TgBot::TgException& e) {
        printf("error: %s\n", e.what());
    }

    return 0;
}
