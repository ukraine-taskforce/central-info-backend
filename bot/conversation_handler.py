import json
import logging

from datetime import datetime
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, Message
from conversation_state import CONV_STATE_TO_CATEGORY, SUPPORT_SUBCATEGORY, END, ERROR, SUPPORT_CATEGORY, START, TIME
from local_providers.state import ConversationState, update_state, set_state, delete_state
from local_providers.reporting import send_report


class ConversationHandler:
    def __init__(self, bot: TeleBot, message: Message):
        self.bot = bot
        self.message = message
        self.language_code = message.from_user.language_code
        self.chat_id = message.chat.id
        self.user_id = message.from_user.id
        self.conversation = json.loads(open("conversation.json").read())

    def __list_messages(self, category, state=None, reply_markup_category=None):
        result = []
        if state is None:
            state = {}

        for message in self.conversation[category]["message"]:
            text = None
            for conditional_text in message.get("conditional_text", []):
                if eval(conditional_text["condition"].format(state=state)):
                    text = conditional_text["text"].get(
                        self.language_code, conditional_text["text"]["en"])
                    break

            if text is None:
                default_text = message.get("text")
                if not default_text:
                    logging.warn(
                        f"No text returned for category {category}. Message: {message}")
                    continue

                text = default_text.get(self.language_code, default_text["en"])

            result.append((text, {}))

        if len(result) == 0:
            logging.warn(f'User action got no reply. Category: {category}')
            return result

        reply_markup_block = self.conversation[reply_markup_category or category]
        if "reply_markup" not in reply_markup_block:
            return result

        markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        for button in reply_markup_block["reply_markup"]:
            if "condition" in button and not eval(button["condition"].format(state=state)):
                continue

            markup.add(KeyboardButton(button["text"].get(self.language_code, button["text"]["en"]),
                                      **button.get("kwargs", {})))

        result.append((result.pop()[0], {"reply_markup": markup}))
        return result

    def __get_button_id(self, category, button_text):
        for button in self.conversation[category].get("reply_markup", []):
            if button["text"].get(self.language_code, button["text"]["en"]) == button_text:
                return button["id"]

    def get_reply_options(self, category):
        for button in self.conversation[category].get("reply_markup", []):
            yield button["text"].get(self.language_code, button["text"]["en"])

    def initialize_next_step(self, state: ConversationState, data, replace_state_with_new_value=False):
        for message_text, kwargs in self.__list_messages(CONV_STATE_TO_CATEGORY[state], data):
            self.bot.send_message(self.chat_id, message_text, **kwargs)

        if replace_state_with_new_value:
            set_state(self.user_id, state, data)
        else:
            update_state(self.user_id, state, data)

    def start(self):
        self.initialize_next_step(
            ConversationState.START, {}, replace_state_with_new_value=True)

    def location(self):
        state = {"user": {"language_code": self.language_code, "id": str(self.user_id)},
                 "support_category": {
                     "location": {
                         "lat": self.message.location.latitude, "lon": self.message.location.longitude},
                     "timestamp": datetime.now().replace(microsecond=0).isoformat()}}

        self.initialize_next_step(ConversationState.SUPPORT_CATEGORY, state, replace_state_with_new_value=True)

    def category(self, state):
        selected_category = self.__get_button_id(
            SUPPORT_CATEGORY, self.message.text)
        state["support_category"]["type"] = selected_category
        logging.info(f'Selected category: {selected_category}')

        self.initialize_next_step(ConversationState.SUPPORT_SUBCATEGORY, state)

    def subcategory(self, state):
        state["support_category"]["support_subcategory"] = self.__get_button_id(
            SUPPORT_SUBCATEGORY, self.message.text)

        self.initialize_next_step(ConversationState.RESULT, state)
        self.result_information(state)

    def result_information(self, state):
        request_category = state["support_category"]["support_subcategory"]
        self.bot.send_message(self.chat_id, f'Results for {self.message.text}:')

    def process_time_details(self, state):
        state["support_category"]["time"] = self.__get_button_id(
            TIME, self.message.text)

        for message_text, kwargs in self.__list_messages(END, state):
            self.bot.send_message(self.chat_id, message_text, **kwargs)

        self.start()

        response = send_report(state)
        logging.info(f"SQS Response: {response}")

    def process_unknown_prompt(self, conv_state: ConversationState, state):
        for message_text, kwargs in self.__list_messages(ERROR, state,
                                                         CONV_STATE_TO_CATEGORY.get(conv_state)):
            self.bot.send_message(self.chat_id, message_text, **kwargs)
