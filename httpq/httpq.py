import enum
from abc import ABC, abstractmethod
from typing import Any, Optional, Union

from toolbox.collections.item import Item, ItemType
from toolbox.collections.mapping import (
    ItemDict,
    ObjectDict,
    OverloadedDict,
    UnderscoreAccessDict,
)


class state(enum.Enum):
    """
    The state of the HTTP request.
    """

    TOP = 0
    HEADER = 1
    BODY = 2

    NEED_MORE_DATA = 4


class Headers(ObjectDict, OverloadedDict, UnderscoreAccessDict, ItemDict):
    def __init__(self, headers: dict = {}):
        super().__init__(headers)

    def _compile(self):
        return b"%s\r\n" % b"".join(
            b"%s: %s\r\n" % (k.raw, v.raw) for k, v in self.items()
        )

    @property
    def raw(self):
        return self._compile()


InpType = Optional[ItemType]
HeadersType = Union[Headers, dict]


class Message(ABC):

    __slots__ = ("protocol", "headers", "body", "state", "buffer")

    def __init__(
        self,
        protocol: InpType = None,
        headers: HeadersType = {},
        body: InpType = None,
    ):
        self.protocol = protocol
        self.headers = headers
        self.body = body

        self.state = state.TOP
        self.buffer = b""

    def __setattr__(self, name: str, value: Any):
        if name == "headers":
            super().__setattr__(name, Headers(value))
        elif name in ("state", "buffer"):
            super().__setattr__(name, value)
        else:
            super().__setattr__(name, Item(value))

    def step_state(self) -> state:

        if not b"\r\n\r\n" in self.buffer:
            self.state = state.NEED_MORE_DATA
            return self.state

        self.state = state.TOP
        _, body = self.buffer.split(b"\r\n\r\n", 1)

        # Split the message into lines.
        for line in self.buffer.split(b"\r\n"):

            # Parses the first line of the HTTP/1.1 msg.
            if self.state == state.TOP:
                self._parse_top(line)
                self.state = state.HEADER

            # Parse the headers of the HTTP/1.1 msg.
            elif self.state == state.HEADER:
                if b":" in line:
                    key, value = line.split(b":", 1)
                    self.headers[key] = value.strip()
                else:
                    self.state = state.BODY

        if self.state == state.BODY:
            self.body = body

        return self.state

    def feed(self, msg: bytes):
        # Checks the msg type:
        if not isinstance(msg, bytes):
            raise TypeError("Message must be bytes.")

        self.buffer += msg

    @abstractmethod
    def _parse_top(self, line: bytes):
        raise NotImplementedError

    @classmethod
    def parse(cls, msg: bytes):
        obj = cls()
        obj.feed(msg)
        return obj

    @abstractmethod
    def _compile_top(self):
        raise NotImplementedError

    def _compile(self):
        return b"%s%s%s" % (self._compile_top(), self.headers.raw, self.body.raw)

    @property
    def raw(self):
        return self._compile()

    def __str__(self):
        if self.__class__ == Request:
            arrow = "→ "
        elif self.__class__ == Response:
            arrow = "← "
        else:
            arrow = "? "

        return arrow + arrow.join(self._compile().decode("utf-8").splitlines(True))


class Request(Message):

    __slots__ = Message.__slots__ + ("method", "target")

    def __init__(
        self,
        method: InpType = None,
        target: InpType = None,
        protocol: InpType = None,
        headers: HeadersType = {},
        body: InpType = None,
    ):
        super().__init__(protocol, headers, body)
        self.method = method
        self.target = target

        objs = [self.method, self.target, self.protocol]
        if all(obj for obj in objs):
            self.state = state.TOP
        elif all(obj == None for obj in objs):
            self.state = state.NEED_MORE_DATA
        else:
            raise ValueError("Request must have method, target, and protocol.")

        if self.headers:
            self.state = state.HEADER

        if self.body:
            self.state = state.BODY

    def _parse_top(self, line: bytes):
        self.method, self.target, self.protocol = line.split(b" ")

    def _compile_top(self):
        return b"%s %s %s\r\n" % (self.method.raw, self.target.raw, self.protocol.raw)


class Response(Message):

    __slots__ = Message.__slots__ + ("status", "reason")

    def __init__(
        self,
        protocol: InpType = None,
        status: InpType = None,
        reason: InpType = None,
        headers: HeadersType = {},
        body: InpType = None,
    ):
        super().__init__(protocol, headers, body)
        self.status = status
        self.reason = reason

        objs = [self.protocol, self.status, self.reason]
        if all(obj for obj in objs):
            self.state = state.TOP
        elif all(obj == None for obj in objs):
            self.state = state.NEED_MORE_DATA
        else:
            raise ValueError("Response must have protocol, status, and reason.")

        if self.headers:
            self.state = state.HEADER

        if self.body:
            self.state = state.BODY

    def _parse_top(self, line: bytes):
        self.protocol, self.status, self.reason = line.split(b" ")

    def _compile_top(self):
        return b"%s %s %s\r\n" % (self.protocol.raw, self.status.raw, self.reason.raw)
