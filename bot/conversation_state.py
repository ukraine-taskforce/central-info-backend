from enum import Enum


class ConversationState(Enum):
    START = 0
    LOCATION = 1
    SUPPORT_CATEGORY = 2
    SUPPORT_SUBCATEGORY = 3
    TIME = 4


START, SUPPORT_CATEGORY, SUPPORT_SUBCATEGORY, TIME, END, ERROR = "start", "support_category", "support_subcategory", "time", "end", "error"
CONV_STATE_TO_CATEGORY = {
    ConversationState.START: START,
    ConversationState.LOCATION: START,
    ConversationState.SUPPORT_CATEGORY: SUPPORT_CATEGORY,
    ConversationState.SUPPORT_SUBCATEGORY: SUPPORT_SUBCATEGORY,
    ConversationState.TIME: TIME
}
