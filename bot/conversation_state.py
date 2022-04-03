from enum import Enum


class ConversationState(Enum):
    START = 0
    LOCATION = 1
    CATEGORY = 2
    LOCATION_DETAILS = 3
    TIME = 4


START, INCIDENT, DISTANCE, TIME, END, ERROR = "start", "incident", "distance", "time", "end", "error"
CONV_STATE_TO_CATEGORY = {
    ConversationState.START: START,
    ConversationState.LOCATION: START,
    ConversationState.CATEGORY: INCIDENT,
    ConversationState.LOCATION_DETAILS: DISTANCE,
    ConversationState.TIME: TIME
}
