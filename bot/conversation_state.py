from enum import Enum


class ConversationState(Enum):
    START = 0
    LOCATION = 1
    SUPPORT_CATEGORY = 2
    SUPPORT_SUBCATEGORY = 3
    RESULT = 4


START, SUPPORT_CATEGORY, SUPPORT_SUBCATEGORY, RESULT, END, ERROR = "start", "support_category", "support_subcategory", "result", "end", "error"
CONV_STATE_TO_CATEGORY = {
    ConversationState.START: START,
    ConversationState.LOCATION: START,
    ConversationState.SUPPORT_CATEGORY: SUPPORT_CATEGORY,
    ConversationState.SUPPORT_SUBCATEGORY: SUPPORT_SUBCATEGORY,
    ConversationState.RESULT: RESULT,
}
