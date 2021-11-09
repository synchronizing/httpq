"""
`httpq` implementation.
"""

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
    States of the HTTP request.
    """

    TOP = 0
    HEADER = 1
    BODY = 2


class Headers(ObjectDict, OverloadedDict, UnderscoreAccessDict, ItemDict):
    """
    Container for HTTP headers.
    """

    def __init__(self, headers: dict = {}):
        """
        Initialize the headers.

        Args:
            headers: The headers to initialize with.
        """
        super().__init__(headers)

    def _compile(self):
        """
        Compile the headers.
        """
        return b"%s\r\n" % b"".join(
            b"%s: %s\r\n" % (k.raw, v.raw) for k, v in self.items()
        )

    @property
    def raw(self):
        """
        The raw headers.
        """
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
        """
        Initializes an HTTP message.

        Args:
            protocol: The protocol of the HTTP message.
            headers: The headers of the HTTP message.
            body: The body of the HTTP message.

        Note:
            :py:class:`Message` is the base class for :py:class:`Request` and
            :py:class:`Response`, and is not intended to be used directly.
        """
        self.protocol = protocol
        self.headers = headers
        self.body = body

        self.state = state.TOP
        self.buffer = b""

    def __setattr__(self, name: str, value: Any):
        """
        Sets the value of the attribute. Defaults to ``toolbox.collections.Item``.

        Args:
            name: The name of the attribute.
            value: The value of the attribute.
        """
        if name == "headers":
            super().__setattr__(name, Headers(value))
        elif name in ("state", "buffer"):
            super().__setattr__(name, value)
        else:
            super().__setattr__(name, Item(value))

    def feed(self, msg: bytes):
        """
        Adds chuncks of the message to the internal buffer.

        Args:
            msg: The message to add to the internal buffer.
        """

        # Checks the msg type:
        if not isinstance(msg, bytes):
            raise TypeError("Message must be bytes.")

        self.buffer += msg

    def step_state(self) -> state:
        """
        Steps the state of state machine.
        """

        if self.buffer.count(b"\r\n") == 0:
            self.state = state.TOP
            return self.state
        elif self.buffer.count(b"\r\n") > 0 and b"\r\n\r\n" not in self.buffer:
            self.state = state.HEADER
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

    @abstractmethod
    def _parse_top(self, line: bytes):  # pragma: no cover
        """
        Parses the first line of the HTTP message.
        """
        raise NotImplementedError

    @classmethod
    def parse(cls, msg: bytes):
        """
        Parses a complete HTTP message.

        Args:
            msg: The message to parse.
        """
        obj = cls()
        obj.feed(msg)
        obj.step_state()
        return obj

    @abstractmethod
    def _compile_top(self):  # pragma: no cover
        """
        Compiles the first line of the HTTP message.
        """
        raise NotImplementedError

    def _compile(self):
        """
        Compiles a complete HTTP message.
        """
        return b"%s%s%s" % (self._compile_top(), self.headers.raw, self.body.raw)

    @property
    def raw(self):
        """
        Returns the raw (bytes) HTTP message.
        """
        return self._compile()

    def __str__(self):
        """
        Pretty-print of the HTTP message.
        """

        if self.__class__ == Request:
            arrow = "→ "
        elif self.__class__ == Response:
            arrow = "← "
        else:  # pragma: no cover
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
        """
        Initializes an HTTP request.

        Args:
            method: The method of the HTTP request.
            target: The target of the HTTP request.
            protocol: The protocol of the HTTP request.
            headers: The headers of the HTTP request.
            body: The body of the HTTP request.
        """
        super().__init__(protocol, headers, body)
        self.method = method
        self.target = target

        objs = [self.method, self.target, self.protocol]
        if all(obj == None for obj in objs):
            self.state = state.TOP
        elif all(obj for obj in objs):
            self.state = state.HEADER
        else:
            raise ValueError("Request must have method, target, and protocol.")

        if self.headers or self.body:
            self.state = state.BODY

    def _parse_top(self, line: bytes):
        """
        Parses the first line of the HTTP request.
        """
        self.method, self.target, self.protocol = line.split(b" ")

    def _compile_top(self):
        """
        Compiles the first line of the HTTP request.
        """
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
        """
        Initializes an HTTP response.

        Args:
            protocol: The protocol of the HTTP response.
            status: The status of the HTTP response.
            reason: The reason of the HTTP response.
            headers: The headers of the HTTP response.
            body: The body of the HTTP response.
        """
        super().__init__(protocol, headers, body)
        self.status = status
        self.reason = reason

        objs = [self.protocol, self.status, self.reason]
        if all(obj == None for obj in objs):
            self.state = state.TOP
        elif all(obj for obj in objs):
            self.state = state.HEADER
        else:
            raise ValueError("Response must have protocol, status, and reason.")

        if self.headers or self.body:
            self.state = state.BODY

    def _parse_top(self, line: bytes):
        """
        Parses the first line of the HTTP response.
        """
        self.protocol, self.status, self.reason = line.split(b" ")

    def _compile_top(self):
        """
        Parses the first line of the HTTP response.
        """
        return b"%s %s %s\r\n" % (self.protocol.raw, self.status.raw, self.reason.raw)
