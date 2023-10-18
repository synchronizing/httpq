##########
Quickstart
##########

`httpq` is a module to parse, modify, and compile HTTP/1.1 messages with a simple built-in state machine. It was build from the ground up with the intention of being quick, simple, and easy to use.

Installing
----------

.. code-block::

    pip install httpq

Using
-----

`httpq` has three methods to initialize a `httpq.Request` and `httpq.Response` object.

:py:meth:`httpq.httpq.Message.__init__`
***************************************

.. code-block:: python

    import httpq

    req = httpq.Request(
        method="GET",
        target="/get",
        protocol="HTTP/1.1",
        headers={"Host": "httpbin.org", "Content-Length": 12},
        body="Hello world!",
    )

    resp = httpq.Response(
        protocol="HTTP/1.1",
        status=200,
        reason="OK",
        headers={"Content-Length": 12},
        body="Hello world!",
    )
    

:py:meth:`httpq.httpq.Message.parse`
************************************

.. code-block:: python

    req = httpq.Request.parse(
        "GET /get HTTP/1.1\r\n"
        "Host: httpbin.org\r\n"
        "Content-Length: 12\r\n"
        "\r\n"
        "Hello world!"
    )

    resp = httpq.Response.parse(
        "HTTP/1.1 200 OK\r\n"
        "Content-Length: 12\r\n"
        "\r\n"
        "Hello world!"
    )

:py:meth:`httpq.httpq.Message.feed`
***************************************

.. code-block:: python

    req = httpq.Request()
    req.feed("GET /get HTTP/1.1\r\n")
    req.feed("Host: httpbin.org\r\n")
    req.feed("Content-Length: 18\r\n")
    req.feed("\r\n")
    req.feed("Hello world!")

    resp = httpq.Response()
    resp.feed("HTTP/1.1 200 OK\r\n")
    resp.feed("Content-Length: 12\r\n")
    resp.feed("\r\n")
    resp.feed("Hello world!") 

The feed mechanism comes with a simple built-in state machine. The state machine can be in one of three states:

* `TOP`: The feed cursor is at the top of the message.
* `HEADER`: The feed cursor is at the headers.
* `BODY`: The feed cursor is at the body.

Once at the body it's the user's responsibility to keep track of the message length.

.. code-block:: python

    import socket
    import httpq

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("httpbin.org", 80))

    req = httpq.Request(
        method="GET",
        target="/get",
        protocol="HTTP/1.1",
        headers={"Host": "httpbin.org"},
    )
    s.sendall(req.raw)

    resp = httpq.Response()
    while resp.state != httpq.state.BODY:
        resp.feed(s.recv(10))

    # At this stage we have a response that has read the top line and headers. It's the user's
    # responsibility to keep track of the rest of the message's length. In this case, we'll just
    # use the `Content-Length` header.
    while len(resp.body) != resp.headers["Content-Length"]:
        body += s.recv(10)

Note that the feed mechanism is used in conjunction with the `state` property. We can use this parse until the body of the message, and then use the captured headers to parse the body.

Modifying and Comparisons
*************************

``httpq`` also comes, out-of-the-box, with an intuitive method to modify and compare message values without caring about type:

.. code-block:: python

    import httpq

    req = httpq.Request(
        method="GET",
        target="/get",
        protocol="HTTP/1.1",
        headers={"Host": "httpbin.org", "Content-Length": 12},
        body="Hello world!",
    )

    resp = httpq.Response(
        protocol="HTTP/1.1",
        status=404,
        reason="Not Found",
        headers={"Content-Length": 12},
        body="Hello world!",
    )

    # string, bytes, and int are all valid values for any field.
    req.method = "POST"
    req.target = b"/"

    resp.status = 200
    resp.reason = "OK"
    resp.headers += {"Accept": "*/*"}

Internally every value of a request or response is saved as an `Item`, a special object type that allows easy setting and comparisons on the fly.

.. code-block::

    resp.status == 200      # >>> True
    resp.status == "200"    # >>> True
    resp.status == b"200"   # >>> True

Once the object is modified to the user's preference utilizing the :py:class:`Request` and :py:class:`Response` object is as easy as calling a property (specifically ``.raw``):

.. code-block:: python

    print(req.raw)
    print(resp.raw)

.. code-block:: 

    b'POST / HTTP/1.1\r\nHost: httpbin.org\r\nContent-Length: 12\r\n\r\nHello world!'
    b'HTTP/1.1 200 OK\r\nContent-Length: 12\r\nAccept: */*\r\n\r\nHello world!'

Uniquely, the :py:meth:`Message.__str__` method returns the objects with arrows to make obvious of its type:

.. code-block:: python

    print(req)
    print(resp)

.. code-block::

    → POST / HTTP/1.1
    → Host: httpbin.org
    → Content-Length: 12
    → 
    → Hello world!

    ← HTTP/1.1 200 OK
    ← Content-Length: 12
    ← Accept: */*
    ← 
    ← Hello world!

Questions & Answers
-------------------

.. _h11: https://github.com/python-hyper/h11
.. |h11| replace:: **h11** 

.. _http-parser: https://github.com/benoitc/http-parser
.. |http-parser| replace:: **http-parser** 

.. _httptools: https://github.com/MagicStack/httptools
.. |httptools| replace:: **httptools** 

**How does this project differ from** |h11|_ **,** |http-parser|_ **, or** |httptools|_ **?**

The intention of this project is to be a simple to use http parser that allows common-sense getting and setting of HTTP values within a message. It is not intended to be a complete implementation of the HTTP protocol like h11, or be a call-back style parser like http-parser and httptools.

**Why another HTTP parser?**

Because while there are many HTTP parsers out in the wild there were none that I thought were intuitive and easy to use. This project is a ~300 line Python module with a simple API and implementation.

It's also intended for the `mitm <https://github.com/synchronizing/mitm>`_ and `night <https://github.com/synchronizing/night>`_ project, and I figured it would be best to have my own implementation to make it easier to manage and maintain.
