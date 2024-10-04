import json
import logging
from datetime import UTC, datetime

from top_assist.models.base import int_pk
from top_assist.models.qa_interaction import QAInteractionDTO, QAInteractionORM

from .database import get_db_session


class InteractionNotFoundError(Exception):  # noqa: D101
    def __init__(self, key: str, value: int_pk | str):
        super().__init__(f"Interaction with {key} {value} not found in the database")


class InteractionCommentNotFoundError(Exception):  # noqa: D101
    def __init__(self, key: str, value: int_pk | str, comment_timestamp: datetime):
        super().__init__(f"Interaction with {key} {value} has no comment for {comment_timestamp}")


class InteractionCommentAlreadyPresentError(Exception):  # noqa: D101
    def __init__(self, key: str, value: int_pk | str, comment_timestamp: datetime):
        super().__init__(f"Interaction with {key} {value} already has a comment for {comment_timestamp}")


def add_question(
    *,
    question: str,
    question_timestamp: datetime,
    thread_id: str,
    channel_id: str,
    slack_user_id: str,
) -> QAInteractionDTO:
    with get_db_session() as session:
        interaction = QAInteractionORM(
            question_text=question,
            question_timestamp=question_timestamp,
            thread_id=thread_id,
            channel_id=channel_id,
            slack_user_id=slack_user_id,
        )
        session.add(interaction)
        session.flush()  # Flush to get the ID
        logging.info("Add QAInteraction", extra={"slack_thread_id": interaction.thread_id})
        return QAInteractionDTO.from_orm(interaction)


def add_answer(
    interaction: QAInteractionDTO,
    *,
    answer: str,
    assistant_thread_id: str | None,
) -> None:
    with get_db_session() as session:
        record = session.get(QAInteractionORM, interaction.interaction_id)
        if not record:
            raise InteractionNotFoundError("id", interaction.slack_thread_id)

        record.answer_text = answer
        record.answer_timestamp = datetime.now(UTC)
        record.assistant_thread_id = assistant_thread_id

        interaction.answer_text = answer
        interaction.assistant_thread_id = assistant_thread_id
        logging.info("Add answer to QAInteraction", extra={"slack_thread_id": record.thread_id})


def mark_answer_posted_on_slack(interaction: QAInteractionDTO) -> None:
    with get_db_session() as session:
        record = session.get(QAInteractionORM, interaction.interaction_id)
        if not record:
            raise InteractionNotFoundError("id", interaction.interaction_id)

        record.answer_posted_on_slack = datetime.now(UTC)
        logging.info("Mark QAInteraction answer as posted on Slack", extra={"slack_thread_id": record.thread_id})


def append_comment(interaction: QAInteractionDTO, *, text: str, author_slack_user_id: str, timestamp: datetime) -> None:
    with get_db_session() as session:
        record = session.get(QAInteractionORM, interaction.interaction_id)
        if not record:
            raise InteractionNotFoundError("id", interaction.interaction_id)

        comments = json.loads(record.comments) if record.comments else []
        target_timestamp = timestamp.isoformat()
        target_comment = next((comment for comment in comments if comment["timestamp"] == target_timestamp), None)
        if target_comment:
            raise InteractionCommentAlreadyPresentError("id", interaction.interaction_id, timestamp)

        comments.append({
            "text": text,
            "user": author_slack_user_id,
            "timestamp": target_timestamp,
        })
        record.comments = json.dumps(comments)
        interaction.comments = record.comments
        logging.info(
            "Append comment to QAInteraction",
            extra={"slack_thread_id": record.thread_id, "comment_timestamp": target_timestamp},
        )


def append_comment_answer(interaction: QAInteractionDTO, *, answer: str, comment_timestamp: datetime) -> None:
    with get_db_session() as session:
        record = session.get(QAInteractionORM, interaction.interaction_id)
        if not record:
            raise InteractionNotFoundError("id", interaction.interaction_id)

        comments = json.loads(record.comments) if record.comments else []
        target_timestamp = comment_timestamp.isoformat()
        target_comment = next((comment for comment in comments if comment["timestamp"] == target_timestamp), None)
        if not target_comment:
            raise InteractionCommentNotFoundError("id", interaction.interaction_id, comment_timestamp)

        target_comment["assistant_response"] = answer
        record.comments = json.dumps(comments)
        interaction.comments = record.comments
        logging.info(
            "Add answer to QAInteraction comment",
            extra={"slack_thread_id": record.thread_id, "comment_timestamp": target_timestamp},
        )


def mark_comment_answer_posted_on_slack(interaction: QAInteractionDTO, *, comment_timestamp: datetime) -> None:
    with get_db_session() as session:
        record = session.get(QAInteractionORM, interaction.interaction_id)
        if not record:
            raise InteractionNotFoundError("id", interaction.interaction_id)

        comments = json.loads(record.comments) if record.comments else []
        target_timestamp = comment_timestamp.isoformat()
        target_comment = next((comment for comment in comments if comment["timestamp"] == target_timestamp), None)
        if not target_comment:
            raise InteractionCommentNotFoundError("id", interaction.interaction_id, comment_timestamp)

        target_comment["assistant_response_posted_on_slack"] = datetime.now(UTC).isoformat()
        record.comments = json.dumps(comments)
        interaction.comments = record.comments
        logging.info(
            "Mark QAInteraction comment answer as posted on Slack",
            extra={"slack_thread_id": record.thread_id, "comment_timestamp": target_timestamp},
        )


def find_by_thread_id(thread_id: str) -> QAInteractionDTO | None:
    with get_db_session() as session:
        record = session.query(QAInteractionORM).filter_by(thread_id=thread_id).first()
        return QAInteractionDTO.from_orm(record) if record else None


def find_by_ids(interaction_ids: list[str]) -> list[QAInteractionDTO]:
    with get_db_session() as session:
        records = session.query(QAInteractionORM).filter(QAInteractionORM.id.in_(interaction_ids)).all()
        return [QAInteractionDTO.from_orm(record) for record in records]


def get_all() -> list[QAInteractionDTO]:
    with get_db_session() as session:
        records = session.query(QAInteractionORM).all()
        return [QAInteractionDTO.from_orm(record) for record in records]


def get_slack_channel_ids() -> list[str]:
    with get_db_session() as session:
        records = session.query(QAInteractionORM.channel_id).distinct().all()
        return [record[0] for record in records]
