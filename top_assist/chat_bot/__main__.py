import top_assist.database.interactions as db_interactions
from top_assist.chat_bot.router import ChatBotRouter
from top_assist.slack.bot_runner import run_bot
from top_assist.utils.tracer import ServiceNames

run_bot(
    router=ChatBotRouter(
        known_question_thread_ids=[interaction.slack_thread_id for interaction in db_interactions.get_all()]
    ),
    trace_service=ServiceNames.chat_bot,
)
