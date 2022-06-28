"""
`httpq` implementation.
"""

import enum
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from toolbox.collections.item import Item, ItemType


class state(enum.Enum):
    """
    States of the HTTP request.
    """

    TOP = 0
    HEADER = 1
    BODY = 2

    INVALID = -1


def convert(i: Union[dict, list, ItemType]) -> Dict[Item, Union[Item, List[Item]]]:
    """
    Recursively converts the input to a dictionary of :py:class:Item.

    Raises:
        TypeError: If the input is not a dictionary, list, or Item type.
    """
    if isinstance(i, dict):
        return {convert(k): convert(v) for k, v in i.items()}
    elif isinstance(i, list):
        return [convert(v) for v in i]
    elif isinstance(i, (bytes, str, int, bool, Item)):
        return Item(i)
    raise TypeError(i)


class Headers(dict):
    """
    Container for HTTP headers.
    """

    def __init__(self, dct: Optional[dict] = None, **kwargs):
        """
        Initializes the headers. Converts the keys & values to :py:class:Item.
        """
        super().__init__(convert(dct), **convert(kwargs))

    def _compile(self) -> bytes:
        """
        Compiles the header.
        """
        bfr = b""
        for k, v in self.items():
            if isinstance(v, Item):
                v = v.raw
            elif isinstance(v, list):
                v = b", ".join((i.raw for i in v))
            bfr += b"%s: %s\r\n" % (k.raw, v)
        return bfr

    @property
    def raw(self) -> bytes:
        """
        Returns the raw (bytes) headers.
        """
        return self._compile()

    def __setitem__(self, key, value):
        """
        Sets new key & values to items.
        """
        if key in self:
            self[Item(key)].append(Item(value))
        else:
            super().__setitem__(Item(key), [Item(value)])

    def __getitem__(self, key: Any) -> Any:
        """
        Allows for case-insensitive, and underscore to dash/space look-up. Returns
         None when no key is found.

        Notes:
            Used in conjunction with :py:meth:`__getattr__` to get headers by name.
            Allows gathering 'X-Foo' as 'headers.X_Foo', 'headers.x_foo',
            'headers.X_FOO'.
        """
        options = [key.replace("_", " "), key.replace("_", "-")]
        options += [option.upper() for option in options]
        options += [option.lower() for option in options]
        options += [option.title() for option in options]

        for option in options:
            if option in self:
                return super().__getitem__(option)

        return None

    def __getattr__(self, key: Any) -> Any:
        if key == "raw":
            return super().__getattribute__(key)

        return self.__getitem__(key)

    def __add__(self, other: dict) -> dict:
        new = {**Headers(self)}
        for k, v in Headers(other).items():
            if k in new:
                new[k] = [new[k], v]
            else:
                new[k] = v
        return new

    def __iadd__(self, other: dict) -> dict:
        self = self.__add__(other)
        return self

    def __sub__(self, other: dict) -> dict:
        new = {**Headers(self)}
        for k, v in Headers(other).items():
            if k in new:
                new[k] = [i for i in new[k] if i not in v]
                if not new[k]:
                    del new[k]
        return Headers(new)

    def __isub__(self, other: dict) -> dict:
        self = self.__sub__(other)
        return self

    def __str__(self) -> str:
        """
        The string representation of the headers.
        """
        return self.raw.decode("utf-8")


InpType = Optional[ItemType]
HeadersType = Union[Headers, dict]


class Message(ABC):

    __slots__ = ("protocol", "headers", "body", "_buffer", "_state")

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

        self._buffer = b""
        self._state = state.TOP

    def __setattr__(self, name: str, value: Any):
        """
        Sets the value of the attribute. Defaults to ``toolbox.collections.Item``.

        Args:
            name: The name of the attribute.
            value: The value of the attribute.
        """
        if name == "headers":
            super().__setattr__(name, Headers(value))
        elif name in ("_buffer", "_state"):
            super().__setattr__(name, value)
        else:
            super().__setattr__(name, Item(value))

    def feed(self, msg: bytes) -> state:
        """
        Adds chuncks of the message to the internal buffer.

        Args:
            msg: The message to add to the internal buffer.
        """

        # Checks the msg type:
        if not isinstance(msg, bytes):
            raise TypeError("Message must be bytes.")

        self._buffer += msg
        return self.state

    @property
    def state(self) -> state:
        """
        Retrieves the state of the HTTP message.
        """

        if self._state == state.INVALID:
            return state.INVALID
        elif self._buffer.count(b"\r\n") > 0 and b"\r\n\r\n" not in self._buffer:
            return state.HEADER
        elif self._buffer.count(b"\r\n") == 0:
            return state.TOP

        self._state = state.TOP
        _, body = self._buffer.split(b"\r\n\r\n", 1)

        # Split the message into lines.
        for line in self._buffer.split(b"\r\n"):

            # Parses the first line of the HTTP/1.1 msg.
            if self._state == state.TOP:
                try:
                    self._parse_top(line)
                except ValueError:
                    self._state = state.INVALID
                    return self._state

                self._state = state.HEADER

            # Parse the headers of the HTTP/1.1 msg.
            elif self._state == state.HEADER:
                if b":" in line:
                    key, value = line.split(b":", 1)
                    self.headers[key] = value.strip()
                else:
                    self._state = state.BODY

        if self._state == state.BODY:
            self.body = body

        return self._state

    @abstractmethod
    def _parse_top(self, line: bytes):  # pragma: no cover
        """
        Parses the first line of the HTTP message.
        """
        raise NotImplementedError

    @classmethod
    def parse(cls, msg: bytes) -> "Message":
        """
        Parses a complete HTTP message.

        Args:
            msg: The message to parse.
        """
        obj = cls()
        obj.feed(msg)
        return obj

    @abstractmethod
    def _compile_top(self) -> bytes:  # pragma: no cover
        """
        Compiles the first line of the HTTP message.
        """
        raise NotImplementedError

    def _compile(self) -> bytes:
        """
        Compiles a complete HTTP message.
        """
        a = self._compile_top()
        b = self.headers.raw
        c = self.body.raw

        return b"%s%s%s" % (a, b, c)

    @property
    def raw(self) -> bytes:
        """
        Returns the raw (bytes) HTTP message.
        """
        return self._compile()

    def __str__(self) -> str:
        """
        Pretty-print of the HTTP message.
        """

        if self._state == state.INVALID:
            return "Invalid Message"

        if self.__class__ == Request:
            arrow = "→ "
        elif self.__class__ == Response:
            arrow = "← "
        else:  # pragma: no cover
            arrow = "? "

        return arrow + arrow.join(self._compile().decode("utf-8").rstrip("\r\n").splitlines(True))


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
            self._buffer = b""
        elif all(obj for obj in objs):
            self._buffer = b"%s %s %s\r\n" % (
                self.method.raw,
                self.target.raw,
                self.protocol.raw,
            )
        else:
            raise ValueError("Request must have method, target, and protocol.")

        if self.headers:
            self._buffer += self.headers.raw + b"\r\n\r\n"

        if self.body:
            self._buffer += self.body.raw

    def _parse_top(self, line: bytes):
        """
        Parses the first line of the HTTP request.
        """
        self.method, self.target, self.protocol = line.split(b" ", 2)

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
            self._buffer = b""
        elif all(obj for obj in objs):
            self._buffer = b"%s %s %s\r\n" % (
                self.protocol.raw,
                self.status.raw,
                self.reason.raw,
            )
        else:
            raise ValueError("Response must have protocol, status, and reason.")

        if self.headers:
            self._buffer += self.headers.raw + b"\r\n\r\n"

        if self.body:
            self._buffer += self.body.raw

    def _parse_top(self, line: bytes):
        """
        Parses the first line of the HTTP response.
        """
        self.protocol, self.status, self.reason = line.split(b" ", 2)

    def _compile_top(self) -> bytes:
        """
        Parses the first line of the HTTP response.
        """
        return b"%s %s %s\r\n" % (self.protocol.raw, self.status.raw, self.reason.raw)
