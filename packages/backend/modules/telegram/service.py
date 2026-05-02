from sqlmodel import Session

from core import telegram_service as shared_telegram_service
from modules.telegram.schemas import ListenerCreate, ListenerResponse, SubscriberResponse


def list_subscribers(session: Session, bot_token: str | None = None) -> list[SubscriberResponse]:
    return [SubscriberResponse.model_validate(item) for item in shared_telegram_service.list_subscribers(session, bot_token)]


def get_subscriber_by_chat(session: Session, chat_id: str, bot_token: str):
    return shared_telegram_service.get_subscriber_by_chat(session, chat_id, bot_token)


def add_subscriber(session: Session, chat_id: str, title: str, bot_token: str) -> SubscriberResponse:
    return SubscriberResponse.model_validate(shared_telegram_service.add_subscriber(session, chat_id, title, bot_token))


def deactivate_subscriber(session: Session, subscriber_id: int) -> None:
    shared_telegram_service.deactivate_subscriber(session, subscriber_id)


def delete_subscriber(session: Session, subscriber_id: int) -> None:
    shared_telegram_service.delete_subscriber(session, subscriber_id)


def list_listeners(
    session: Session,
    subscriber_id: int | None = None,
    datasource_id: str | None = None,
) -> list[ListenerResponse]:
    return [ListenerResponse.model_validate(item) for item in shared_telegram_service.list_listeners(session, subscriber_id, datasource_id)]


def add_listener(session: Session, data: ListenerCreate) -> ListenerResponse:
    created = shared_telegram_service.add_listener(
        session,
        shared_telegram_service.ListenerCreate.model_validate(data.model_dump()),
    )
    return ListenerResponse.model_validate(created)


def remove_listener(session: Session, listener_id: int) -> None:
    shared_telegram_service.remove_listener(session, listener_id)


def auto_populate_listeners(session: Session, datasource_id: str) -> list[ListenerResponse]:
    return [ListenerResponse.model_validate(item) for item in shared_telegram_service.auto_populate_listeners(session, datasource_id)]


def get_notification_chat_ids(session: Session, datasource_id: str) -> list[tuple[str, str]]:
    return shared_telegram_service.get_notification_chat_ids(session, datasource_id)
