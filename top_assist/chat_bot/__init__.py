from top_assist.auth.sign_in_flow import register_sign_in_context_operation

from .tasks.question import QuestionEvent, process_question

register_sign_in_context_operation(QuestionEvent, process_question)
