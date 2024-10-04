from top_assist.semantic_router.tools.prompt_optimizer import query_prompt_optimizer
from top_assist.semantic_router.tools.query_chatgpt import query_chatgpt
from top_assist.semantic_router.tools.query_knowledge_base import query_knowledge_base
from top_assist.semantic_router.tools.web_search import web_search

tools = [web_search, query_chatgpt, query_prompt_optimizer, query_knowledge_base]
