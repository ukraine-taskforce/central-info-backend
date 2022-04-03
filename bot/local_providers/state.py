import json
import os

from conversation_state import ConversationState

__conversation_key = "Conversation"
__data_key = "Data"


def get_file_name(user_id):
    return f"state-{user_id}.json"


def get_state(user_id):
    with open(get_file_name(user_id), "r+") as file:
        file.seek(0)
        content = file.read()

    user_state = json.loads(content or '{}')
    conversation_state = user_state.get(
        __conversation_key) or ConversationState.START.value
    return ConversationState(conversation_state), user_state.get(__data_key) or {}


def set_state(user_id, state: ConversationState, data):
    with open(get_file_name(user_id), "w+") as file:
        content = file.read()
        user_state = json.loads(content or '{}')
        user_state[__conversation_key] = state.value
        user_state[__data_key] = data
        updated_content = json.dumps(user_state)
        file.seek(0)
        file.write(updated_content)
        file.truncate()


def update_state(user_id, state: ConversationState, data):
    set_state(user_id, state, data)


def delete_state(user_id):
    set_state(user_id, ConversationState.START, {})
