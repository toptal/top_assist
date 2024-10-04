from top_assist.utils.tracer import ServiceNames, tracer

from ._client import ChannelInfo, WebClient


@tracer.wrap(service=ServiceNames.slack.value)
def get_channel(channel: str) -> ChannelInfo | None:
    return WebClient.default().get_channel(channel)


@tracer.wrap(service=ServiceNames.slack.value)
def leave_channel(channel_id: str) -> bool:
    return WebClient.default().leave_channel(channel_id)
