#############
State Machine
#############

``httpq`` comes with a state machine that can be used to control a stream of data coming in from a socket, or socket-like object (io). A :py:class:`httpq.httpq.Message` has an internal variable called ``state`` that is used to keep track of the state of the message. There are four states, as defined in :py:class:`httpq.httpq.state`:

.. autoclass:: httpq.httpq.state
    :members:

    * ``TOP``: Message is at the top line.
    * ``HEADERS``: Message is in the headers.
    * ``BODY``: Message is in the body.

These states are used to determine how to handle the data that comes in from an io. Note that the state the message is in is its *current state* - that is to say, a ``Message`` starts in the ``TOP`` state and as data is fed into it, it will change state from ``TOP`` to ``HEADERS`` to ``BODY``.

Since ``httpq`` is not a complete HTTP/1.1 tool it does not know when the body of the message has reached its end. Therefore, it's the job of the user to determine when the message is complete by either looking at the ``Content-Length`` or ``Transfer-Encoding`` header.

Examples
--------

Say you would like to send a request to a server, and receive back its response in full. To do this, you would do the following:

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
    while resp.step_state() != httpq.state.BODY:
        resp.feed(s.recv(10))

    while len(resp.body) != resp.headers["Content-Length"]:
        resp.body += s.recv(10)

Take note of a few things. First, note how we receive the response in chunks (bytes of 10 for sake of example), and how we keep track of when we reach the body:

.. code-block:: python

    ...
    resp = httpq.Response()
    while resp.step_state() != httpq.state.BODY:
        resp.feed(s.recv(10))
    ...

The method in which we use to step the state machine (and in turn receive the current state of the message) is ``step_state``. This method returns the current state of the message, and can be used to determine how to handle the data as it comes in. For the sake of example, if we print out the current state of the message and its buffer we would see the following output:

.. code-block:: python

    ...
    resp = httpq.Response()
    while resp.step_state() != httpq.state.BODY:
        print(resp.state, resp.buffer)
        resp.feed(s.recv(10))

    print(resp.state, resp.buffer)
    ...

.. code-block::

    state.TOP b''
    state.TOP b'HTTP/1.1 2'
    state.HEADER b'HTTP/1.1 200 OK\r\nDat'
    state.HEADER b'HTTP/1.1 200 OK\r\nDate: Tue, 09'
    state.HEADER b'HTTP/1.1 200 OK\r\nDate: Tue, 09 Nov 2021 '
    state.HEADER b'HTTP/1.1 200 OK\r\nDate: Tue, 09 Nov 2021 18:29:18 G'
    state.HEADER b'HTTP/1.1 200 OK\r\nDate: Tue, 09 Nov 2021 18:29:18 GMT\r\nConten'
    state.HEADER b'HTTP/1.1 200 OK\r\nDate: Tue, 09 Nov 2021 18:29:18 GMT\r\nContent-Type: ap'
    state.HEADER b'HTTP/1.1 200 OK\r\nDate: Tue, 09 Nov 2021 18:29:18 GMT\r\nContent-Type: application/'
    state.HEADER b'HTTP/1.1 200 OK\r\nDate: Tue, 09 Nov 2021 18:29:18 GMT\r\nContent-Type: application/json\r\nCont'
    state.HEADER b'HTTP/1.1 200 OK\r\nDate: Tue, 09 Nov 2021 18:29:18 GMT\r\nContent-Type: application/json\r\nContent-Length'
    state.HEADER b'HTTP/1.1 200 OK\r\nDate: Tue, 09 Nov 2021 18:29:18 GMT\r\nContent-Type: application/json\r\nContent-Length: 197\r\nCon'
    state.HEADER b'HTTP/1.1 200 OK\r\nDate: Tue, 09 Nov 2021 18:29:18 GMT\r\nContent-Type: application/json\r\nContent-Length: 197\r\nConnection: k'
    state.HEADER b'HTTP/1.1 200 OK\r\nDate: Tue, 09 Nov 2021 18:29:18 GMT\r\nContent-Type: application/json\r\nContent-Length: 197\r\nConnection: keep-alive\r'
    state.HEADER b'HTTP/1.1 200 OK\r\nDate: Tue, 09 Nov 2021 18:29:18 GMT\r\nContent-Type: application/json\r\nContent-Length: 197\r\nConnection: keep-alive\r\nServer: g'
    state.HEADER b'HTTP/1.1 200 OK\r\nDate: Tue, 09 Nov 2021 18:29:18 GMT\r\nContent-Type: application/json\r\nContent-Length: 197\r\nConnection: keep-alive\r\nServer: gunicorn/19'
    state.HEADER b'HTTP/1.1 200 OK\r\nDate: Tue, 09 Nov 2021 18:29:18 GMT\r\nContent-Type: application/json\r\nContent-Length: 197\r\nConnection: keep-alive\r\nServer: gunicorn/19.9.0\r\nAcce'
    state.HEADER b'HTTP/1.1 200 OK\r\nDate: Tue, 09 Nov 2021 18:29:18 GMT\r\nContent-Type: application/json\r\nContent-Length: 197\r\nConnection: keep-alive\r\nServer: gunicorn/19.9.0\r\nAccess-Control'
    state.HEADER b'HTTP/1.1 200 OK\r\nDate: Tue, 09 Nov 2021 18:29:18 GMT\r\nContent-Type: application/json\r\nContent-Length: 197\r\nConnection: keep-alive\r\nServer: gunicorn/19.9.0\r\nAccess-Control-Allow-Ori'
    state.HEADER b'HTTP/1.1 200 OK\r\nDate: Tue, 09 Nov 2021 18:29:18 GMT\r\nContent-Type: application/json\r\nContent-Length: 197\r\nConnection: keep-alive\r\nServer: gunicorn/19.9.0\r\nAccess-Control-Allow-Origin: *\r\nAc'
    state.HEADER b'HTTP/1.1 200 OK\r\nDate: Tue, 09 Nov 2021 18:29:18 GMT\r\nContent-Type: application/json\r\nContent-Length: 197\r\nConnection: keep-alive\r\nServer: gunicorn/19.9.0\r\nAccess-Control-Allow-Origin: *\r\nAccess-Contr'
    state.HEADER b'HTTP/1.1 200 OK\r\nDate: Tue, 09 Nov 2021 18:29:18 GMT\r\nContent-Type: application/json\r\nContent-Length: 197\r\nConnection: keep-alive\r\nServer: gunicorn/19.9.0\r\nAccess-Control-Allow-Origin: *\r\nAccess-Control-Allow-C'
    state.HEADER b'HTTP/1.1 200 OK\r\nDate: Tue, 09 Nov 2021 18:29:18 GMT\r\nContent-Type: application/json\r\nContent-Length: 197\r\nConnection: keep-alive\r\nServer: gunicorn/19.9.0\r\nAccess-Control-Allow-Origin: *\r\nAccess-Control-Allow-Credentials'
    state.BODY b'HTTP/1.1 200 OK\r\nDate: Tue, 09 Nov 2021 18:29:18 GMT\r\nContent-Type: application/json\r\nContent-Length: 197\r\nConnection: keep-alive\r\nServer: gunicorn/19.9.0\r\nAccess-Control-Allow-Origin: *\r\nAccess-Control-Allow-Credentials: true\r\n\r\n'

Once we have reached the `BODY` state, there are no further states. This is useful because it allows the user to dictate how much data to read from the io, and if need be how the handle that incoming data. This leads us into the second note: notice how the body is then gathered:

.. code-block:: python

    while len(resp.body) != resp.headers["Content-Length"]:
        resp.body += s.recv(10)

In this specific case we have decided to store the body into memory, and have (assumed) the server will always respond with ``Content-Length`` as a header. This is a very naive approach, and is not recommended for more complex applications- however, it serves as a good example of how one can then use a message in the `BODY` state to continue reading data from the io.
