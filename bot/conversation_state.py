from enum import Enum


class ConversationState(Enum):
    START = 0
    REQUEST_LOCATION = 10
    LOCATION = 20
    LOCATION_ERROR = 30
    SUPPORT_CATEGORY = 40
    SUPPORT_SUBCATEGORY = 50
    RESULTS_PAGE = 60
    SUGGEST_LOCATION_CHANGE = 70


START, LOCATION_ERROR, REQUEST_LOCATION, SUPPORT_CATEGORY, SUPPORT_SUBCATEGORY, RESULTS_PAGE, SUGGEST_LOCATION_CHANGE, END, ERROR = "start", "location_error", "request_location", "support_category", "support_subcategory", "results", "suggest_location_change", "end", "error"
CONV_STATE_TO_CATEGORY = {
    ConversationState.START: START,
    ConversationState.REQUEST_LOCATION: REQUEST_LOCATION,
    ConversationState.LOCATION_ERROR: LOCATION_ERROR,
    ConversationState.SUPPORT_CATEGORY: SUPPORT_CATEGORY,
    ConversationState.SUPPORT_SUBCATEGORY: SUPPORT_SUBCATEGORY,
    ConversationState.RESULTS_PAGE: RESULTS_PAGE,
    ConversationState.SUGGEST_LOCATION_CHANGE: SUGGEST_LOCATION_CHANGE,
}
CATEGORY_TO_CONV_STATE = {v: k for k, v in CONV_STATE_TO_CATEGORY.items()}
