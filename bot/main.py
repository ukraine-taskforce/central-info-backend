import logging
import os
import json
from conversation_state import DISTANCE, INCIDENT, TIME

from conversation_handler import ConversationHandler

from telebot.types import Update

from local_providers.state import ConversationState, get_state
from bot import init_bot
from network import from_telegram_network, is_direct_invocation

run_local = True

bot = init_bot()

logging.getLogger().setLevel(logging.INFO)


def lambda_handler(event: dict, context):
    request = event["body"]
    if isinstance(request, str):
        request = json.loads(request)

    if request.get("setWebhook", False) and is_direct_invocation(event):
        bot.remove_webhook()
        webhook = f"{os.environ['domain']}/{os.environ['path_key']}/webhook/"
        bot.set_webhook(url=webhook)
        return {'statusCode': 200}

    if event.get('rawPath') == f"/{os.environ['path_key']}/send_message/":
        to_user = request["telegramUID"]
        bot.send_message(to_user, request["text"])
        return {'statusCode': 200}

    if event.get('rawPath') != f"/{os.environ['path_key']}/webhook/":
        return {'statusCode': 404}

    if not from_telegram_network(event["headers"]["x-forwarded-for"]):
        return {'statusCode': 403}

    update = Update.de_json(request)
    handle_message(update.message)

    return {'statusCode': 200}


@bot.message_handler(func=lambda _: True, content_types=['text', 'location'])
def handle_message(message):
    logging.info(f'Handling message "{message}"')
    if not message:
        return

    conv_handler = ConversationHandler(bot, message)
    if message.text == '/start':
        conv_handler.start()
        return

    conv_state, state = get_state(message.from_user.id)
    logging.info(f'State: {conv_state}, {state}')
    if message.location:
        conv_handler.location()
    elif message.text in conv_handler.get_reply_options(INCIDENT) and conv_state == ConversationState.CATEGORY:
        conv_handler.category(state)
    elif message.text in conv_handler.get_reply_options(
            DISTANCE) and conv_state == ConversationState.LOCATION_DETAILS:
        conv_handler.process_location_details(state)
    elif message.text in conv_handler.get_reply_options(TIME) and conv_state == ConversationState.TIME:
        conv_handler.process_time_details(state)
    else:
        conv_handler.process_unknown_prompt(conv_state, state)


if run_local:
    logging.info('Bot started...')
    bot.infinity_polling()
