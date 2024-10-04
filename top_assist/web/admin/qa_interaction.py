from collections.abc import Sequence

from starlette_admin import BaseField, DateTimeField, StringField
from starlette_admin.contrib.sqla import ModelView

from top_assist.models import QAInteractionORM
from top_assist.web.admin.mixins import ForbiddenActionsMixin


class QAInteractionAdmin(ForbiddenActionsMixin, ModelView):
    """Admin view for QA interactions."""

    page_size = 100

    fields: Sequence[BaseField] = [
        StringField("id"),
        StringField("question_text"),
        DateTimeField("question_timestamp"),
        StringField("answer_text"),
        DateTimeField("answer_timestamp"),
        DateTimeField("answer_posted_on_slack"),
        StringField("channel_id"),
        StringField("slack_user_id"),
        StringField("comments"),
        StringField("thread_id", exclude_from_list=True),
        StringField("assistant_thread_id", exclude_from_list=True),
    ]

    searchable_fields: Sequence[str] = ["channel_id", "slack_user_id"]

    sortable_fields: Sequence[str] = [
        "id",
        "channel_id",
        "slack_user_id",
        "question_timestamp",
        "answer_timestamp",
        "thread_id",
    ]


qa_interaction_view = QAInteractionAdmin(
    QAInteractionORM,
    label="QA Interactions",
    name="QA Interactions",
    identity="qa_interactions",
    icon="fa-sharp fa-regular fa-comments",
)
