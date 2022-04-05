from enum import Enum


class ConversationState(Enum):
    START = 0
    REQUEST_LOCATION = 1
    LOCATION = 2
    SUPPORT_CATEGORY = 3
    SUPPORT_SUBCATEGORY = 4
    RESULTS_PAGE = 5
    SUGGEST_LOCATION_CHANGE = 6


START, REQUEST_LOCATION, SUPPORT_CATEGORY, SUPPORT_SUBCATEGORY, RESULTS_PAGE, SUGGEST_LOCATION_CHANGE, END, ERROR = "start", "request_location", "support_category", "support_subcategory", "results", "suggest_location_change", "end", "error"
CONV_STATE_TO_CATEGORY = {
    ConversationState.START: START,
    ConversationState.REQUEST_LOCATION: REQUEST_LOCATION,
    ConversationState.LOCATION: START,
    ConversationState.SUPPORT_CATEGORY: SUPPORT_CATEGORY,
    ConversationState.SUPPORT_SUBCATEGORY: SUPPORT_SUBCATEGORY,
    ConversationState.RESULTS_PAGE: RESULTS_PAGE,
    ConversationState.SUGGEST_LOCATION_CHANGE: SUGGEST_LOCATION_CHANGE,
}
CATEGORY_TO_CONV_STATE = {v: k for k, v in CONV_STATE_TO_CATEGORY.items()}
