from email import message
from functools import reduce
import json
import logging

from datetime import datetime
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, Message
from geo_api.geo_helpers import get_location_by_coordinates, get_distance, get_map_link
from text_translations import t, set_localization
from information_node import InformationNode
from get_file_content import get_file_content
from conversation_state import CATEGORY_TO_CONV_STATE, CONV_STATE_TO_CATEGORY, RESULTS_PAGE, SUGGEST_LOCATION_CHANGE, SUPPORT_SUBCATEGORY, ERROR, SUPPORT_CATEGORY
from local_providers.get_centralized_info import get_centralized_info
from local_providers.get_supported_countries import get_supported_countries
from local_providers.state import ConversationState, update_state, set_state


class ConversationHandler:
    def __init__(self, bot: TeleBot, message: Message):
        self.__results_page_size = 3
        self.bot = bot
        self.message = message
        self.language_code = message.from_user.language_code
        # afaik should work for synchronous scenarios
        # where an instance is created per thread
        set_localization(self.language_code)

        self.chat_id = message.chat.id
        self.user_id = message.from_user.id
        self.conversation = json.loads(open("conversation.json").read())
        self.supported_countries = get_supported_countries()

    def __list_messages(self, category, state=None, reply_markup_category=None, format_message_args_map={}):
        result = []
        if state is None:
            state = {}

        for message in self.conversation[category]["message"]:
            text = None
            for conditional_text in message.get("conditional_text", []):
                if eval(conditional_text["condition"].format(state=state)):
                    text = t(conditional_text["text_key"])
                    break

            if text is None:
                default_text = message.get("text_key")
                text = None if not default_text else t(default_text)
                if not text:
                    logging.warn(
                        f"No text returned for category {category}. Message: {message}")
                    continue

            result.append((text.format_map(format_message_args_map), {}))

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

            markup.add(KeyboardButton(
                t(button["text_key"]), **button.get("kwargs", {})))

        result.append((result.pop()[0], {"reply_markup": markup}))
        return result

    def __get_button_id(self, category, button_text):
        for button in self.conversation[category].get("reply_markup", []):
            if t(button["text_key"]) == button_text:
                return button["id"]

    def __send_response_message(self, message: str, **kwargs):
        self.bot.send_message(self.chat_id, message,
                              parse_mode='Markdown', **kwargs)

    def __is_country_supported(self, country_code: str):
        return country_code.upper() in self.supported_countries

    def get_reply_options(self, category):
        for button in self.conversation[category].get("reply_markup", []):
            yield t(button["text_key"])

    def initialize_next_step(self, state: ConversationState, data, replace_state_with_new_value=False, format_message_args_map={}):
        for message_text, kwargs in self.__list_messages(CONV_STATE_TO_CATEGORY[state], data, format_message_args_map=format_message_args_map):
            self.__send_response_message(message_text, **kwargs)

        if replace_state_with_new_value:
            set_state(self.user_id, state, data)
        else:
            update_state(self.user_id, state, data)

    def start(self):
        self.initialize_next_step(
            ConversationState.START, {}, replace_state_with_new_value=True)
        self.initialize_next_step(ConversationState.REQUEST_LOCATION, {})

    def location(self):
        shared_coordinates = self.message.location
        geo_location = get_location_by_coordinates(
            shared_coordinates.latitude, shared_coordinates.longitude)
        if not geo_location:
            self.__send_response_message(t("location_error"))
            return

        if not self.__is_country_supported(geo_location["country_code"]):
            self.__send_response_message(t("unsupported_location").format(
                country=geo_location["country_name"]))
            return

        state = {
            "user": {
                "language_code": self.language_code,
                "id": str(self.user_id),
                "location": geo_location,
                "timestamp": datetime.now().replace(microsecond=0).isoformat()
            },
            "request": {}
        }

        self.initialize_next_step(
            ConversationState.SUPPORT_CATEGORY, state, replace_state_with_new_value=True)

    def category(self, state):
        selected_category = self.__get_button_id(
            SUPPORT_CATEGORY, self.message.text)
        state["request"]["support_category"] = selected_category

        self.initialize_next_step(ConversationState.SUPPORT_SUBCATEGORY, state)

    def subcategory(self, state):
        selected_category = self.__get_button_id(
            SUPPORT_SUBCATEGORY, self.message.text)
        state["request"]["support_subcategory"] = {
            "id": selected_category,
            "name": self.message.text
        }
        state["results"] = {"page": 0, "can_load_more": True}

        update_state(self.user_id, ConversationState.RESULTS_PAGE, state)
        self.results_page(state)

    def results_page(self, state):
        page = state["results"]["page"]
        next_action = None if page == 0 else self.__get_button_id(
            RESULTS_PAGE, self.message.text).lower()
        if next_action == SUGGEST_LOCATION_CHANGE:
            self.initialize_next_step(
                ConversationState.SUGGEST_LOCATION_CHANGE, state)
            return

        # load page data
        request_category = state["request"]["support_subcategory"]
        location_country_code = state["user"]["location"]["country_code"]
        data, can_load_more = get_centralized_info(
            location_country_code, request_category["id"], self.__results_page_size, page)
        format_args = {
            "category": request_category["name"]
        }

        state["results"]["page"] = page + 1
        state["results"]["can_load_more"] = can_load_more

        # render cards by template
        node_template = get_file_content('templates/information_node.template')

        location = state["user"]["location"]
        user_coordinates = (location["latitude"], location["longitude"])

        def map_information_node(node_json):
            coordinates = (node_json["Latitude"], node_json["Longitude"])
            return InformationNode(
                node_json["ID"], get_distance(
                    user_coordinates, coordinates),
                f'[{t("website")}]({node_json["Hyperlink"]})',
                f'[{t("map")}]({get_map_link(coordinates)})',
                node_json["Category"])

        mapped_data = map(map_information_node, data)
        nodes = '\n'.join(
            map(lambda x: node_template.format_map(x.to_map()), mapped_data))

        header = t("results_for_category") if page == 0 else t(
            "more_results_for_category")
        format_args = {
            "card_header": header.format(category=request_category["name"]),
            "card_content": nodes,
            "card_footer": '' if can_load_more else t("no_more_results_available")
        }
        self.initialize_next_step(
            ConversationState.RESULTS_PAGE, state, format_message_args_map=format_args)

    def suggest_location_change(self, state):
        next_state = self.__get_button_id(
            SUGGEST_LOCATION_CHANGE, self.message.text).lower()
        self.initialize_next_step(
            CATEGORY_TO_CONV_STATE[next_state], state)

    def process_unknown_prompt(self, conv_state: ConversationState, state):
        for message_text, kwargs in self.__list_messages(ERROR, state,
                                                         CONV_STATE_TO_CATEGORY.get(conv_state)):
            self.bot.send_message(self.chat_id, message_text, **kwargs)
