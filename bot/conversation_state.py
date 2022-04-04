from enum import Enum


class ConversationState(Enum):
    START = 0
    LOCATION = 1
    SUPPORT_CATEGORY = 2
    SUPPORT_SUBCATEGORY = 3
    RESULTS_PAGE = 4
    SUGGEST_LOCATION_CHANGE = 5


START, SUPPORT_CATEGORY, SUPPORT_SUBCATEGORY, RESULTS_PAGE, SUGGEST_LOCATION_CHANGE, END, ERROR = "start", "support_category", "support_subcategory", "results", "suggest_location_change", "end", "error"
CONV_STATE_TO_CATEGORY = {
    ConversationState.START: START,
    ConversationState.LOCATION: START,
    ConversationState.SUPPORT_CATEGORY: SUPPORT_CATEGORY,
    ConversationState.SUPPORT_SUBCATEGORY: SUPPORT_SUBCATEGORY,
    ConversationState.RESULTS_PAGE: RESULTS_PAGE,
    ConversationState.SUGGEST_LOCATION_CHANGE: SUGGEST_LOCATION_CHANGE,
}
