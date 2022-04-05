import json
import logging

from datetime import datetime
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, Message
from information_node import InformationNode
from get_file_content import get_file_content
from conversation_state import CONV_STATE_TO_CATEGORY, RESULTS_PAGE, SUGGEST_LOCATION_CHANGE, SUPPORT_SUBCATEGORY, ERROR, SUPPORT_CATEGORY
from local_providers.get_centralized_info import get_centralized_info
from local_providers.state import ConversationState, update_state, set_state
from local_providers.reporting import send_report


class ConversationHandler:
    def __init__(self, bot: TeleBot, message: Message):
        self.__results_page_size = 3
        self.bot = bot
        self.message = message
        self.language_code = message.from_user.language_code
        self.chat_id = message.chat.id
        self.user_id = message.from_user.id
        self.conversation = json.loads(open("conversation.json").read())

    def __list_messages(self, category, state=None, reply_markup_category=None, format_message_args_map={}):
        result = []
        if state is None:
            state = {}

        for message in self.conversation[category]["message"]:
            text = None
            for conditional_text in message.get("conditional_text", []):
                if eval(conditional_text["condition"].format(state=state)):
                    text = conditional_text["text"].get(
                        self.language_code, conditional_text["text"]["en"]).format_map(
                            format_message_args_map)
                    break

            if text is None:
                default_text = message.get("text")
                if not default_text:
                    logging.warn(
                        f"No text returned for category {category}. Message: {message}")
                    continue

                text = default_text.get(self.language_code, default_text["en"]).format_map(
                    format_message_args_map
                )

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

    def initialize_next_step(self, state: ConversationState, data, replace_state_with_new_value=False, format_message_args_map={}):
        for message_text, kwargs in self.__list_messages(CONV_STATE_TO_CATEGORY[state], data, format_message_args_map=format_message_args_map):
            self.bot.send_message(self.chat_id, message_text, **kwargs)

        if replace_state_with_new_value:
            set_state(self.user_id, state, data)
        else:
            update_state(self.user_id, state, data)

    def start(self):
        self.initialize_next_step(
            ConversationState.START, {}, replace_state_with_new_value=True)

    def location(self):
        logging.info(f'Location received: {self.message.location}')
        state = {"user": {"language_code": self.language_code, "id": str(self.user_id)},
                 "support_category": {
                     "location": {
                         "lat": self.message.location.latitude, "lon": self.message.location.longitude},
                     "timestamp": datetime.now().replace(microsecond=0).isoformat()}}

        self.initialize_next_step(
            ConversationState.SUPPORT_CATEGORY, state, replace_state_with_new_value=True)

    def category(self, state):
        selected_category = self.__get_button_id(
            SUPPORT_CATEGORY, self.message.text)
        state["support_category"]["type"] = selected_category

        self.initialize_next_step(ConversationState.SUPPORT_SUBCATEGORY, state)

    def subcategory(self, state):
        selected_category = self.__get_button_id(
            SUPPORT_SUBCATEGORY, self.message.text)
        state["support_category"]["support_subcategory"] = {
            "id": selected_category,
            "name": self.message.text
        }
        state["results"] = {"page": 0, "can_load_more": True}

        update_state(self.user_id, ConversationState.RESULTS_PAGE, state)
        self.results_page(state)

    def results_page(self, state):
        page = state["results"]["page"]
        next_action = None if page == 0 else self.__get_button_id(
            RESULTS_PAGE, self.message.text)
        if next_action == SUGGEST_LOCATION_CHANGE:
            self.initialize_next_step(
                ConversationState.SUGGEST_LOCATION_CHANGE, state)
            return

        # load page data
        request_category = state["support_category"]["support_subcategory"]
        data, can_load_more = get_centralized_info(
            "TODO", request_category["id"], self.__results_page_size, page)
        format_args = {
            "category": request_category["name"]
        }

        state["results"]["page"] = page + 1
        self.initialize_next_step(
            ConversationState.RESULTS_PAGE, state, format_message_args_map=format_args)

        # render cards by template
        card_template = get_file_content('templates/information_card.template')
        node_template = get_file_content('templates/information_node.template')

        mapped_data = map(lambda x: InformationNode(
            x["ID"], 25, x["Hyperlink"], "maplink", x["Category"]), data)
        nodes = '\n'.join(
            map(lambda x: node_template.format_map(x.to_map()), mapped_data))
        message_content = {
            "header": "header",
            "content": nodes,
            "footer": "footer"
        }
        message = card_template.format_map(message_content)
        self.bot.send_message(
            self.chat_id, message, reply_markup=ReplyKeyboardRemove())

    def process_unknown_prompt(self, conv_state: ConversationState, state):
        for message_text, kwargs in self.__list_messages(ERROR, state,
                                                         CONV_STATE_TO_CATEGORY.get(conv_state)):
            self.bot.send_message(self.chat_id, message_text, **kwargs)
