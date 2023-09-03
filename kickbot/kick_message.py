import json


class KickMessage:
    def __init__(self, raw_data: str):
        data = json.loads(raw_data)
        self.data = data
        self.id: str | None = data.get('id')
        self.chatroom_id: int | None = data.get('chatroom_id')
        self.content: str | None = data.get('content')
        self.args: list[str] | None = self.content.split()
        self.type: str | None = data.get('type')
        self.created_at: str | None = data.get('created_at')
        self.sender: _Sender | None = _Sender(data.get('sender'))

    def __repr__(self) -> str:
        return f"KickMessage({self.data})"


class _Sender:
    def __init__(self, raw_sender: dict) -> None:
        self.raw_sender = raw_sender
        self.user_id: int | None = raw_sender.get('id')
        self.username: str | None = raw_sender.get('username')
        self.slug: str | None = raw_sender.get('slug')
        self.identity: dict = raw_sender.get('identity')
        self.badges: list = self.identity.get('badges')

    def __repr__(self) -> str:
        return f"KickMessage.sender({self.raw_sender})"
