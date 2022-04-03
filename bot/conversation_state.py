from enum import Enum


class ConversationState(Enum):
    START = 0
    LOCATION = 1
    SUPPORT_CATEGORY = 2
    SUPPORT_SUBCATEGORY = 3
    RESULTS_PAGE = 4


START, SUPPORT_CATEGORY, SUPPORT_SUBCATEGORY, RESULTS_PAGE, END, ERROR = "start", "support_category", "support_subcategory", "results", "end", "error"
CONV_STATE_TO_CATEGORY = {
    ConversationState.START: START,
    ConversationState.LOCATION: START,
    ConversationState.SUPPORT_CATEGORY: SUPPORT_CATEGORY,
    ConversationState.SUPPORT_SUBCATEGORY: SUPPORT_SUBCATEGORY,
    ConversationState.RESULTS_PAGE: RESULTS_PAGE,
}
