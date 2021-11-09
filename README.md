# 💨 httpq

A module to parse, modify, and compile HTTP/1.1 messages with a simple built-in state machine.

## Installing

```
pip install httpq
```

## Documentation

Documentation can be found [here]().

## Using

`httpq` is intended as a lightweight HTTP/1.1 parser and compiler. `httpq`'s job is to ensure that the message is properly structure, and give user access to an easy-to-use interface to view, manipulate, and compile HTTP messages. It is the job of the user to use `httpq` to perform HTTP/1.1 specific tasks.

`httpq` has three different ways to initialize a `Request` or `Response` object:

#### `__init__`

```python
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
```

#### `parse`

```python
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
```

Notice that `parse` takes a full message.

#### `feed`

```python
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
```

The feed mechanism is useful when you want to parse a message in chunks, and manage a socket connection.

```python
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

body = resp.body
while len(body) != resp.headers["Content-Length"]:
    body += s.recv(10)
```

Note that we used the `step_state` method to advance the state machine until we reached the body, and thereafter, we read from the socket until the body is complete.

`httpq` also comes, out-of-the-box, with an intuitive method to modify and compare message values without caring about type:

```python
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
```

Internally every value of a request or response is saved as an `Item`, a special object type that allows easy setting and comparisons on the fly.

```python
resp.status == 200      # >>> True
resp.status == "200"    # >>> True
resp.status == b"200"   # >>> True
```

Once the object is modified to the user's preference utilizing the `Request` and `Response` object is as easy as calling a property (specifically .raw):

```python
print(req.raw)
print(resp.raw)
```

```
b'POST / HTTP/1.1\r\nHost: httpbin.org\r\nContent-Length: 12\r\n\r\nHello world!'
b'HTTP/1.1 200 OK\r\nContent-Length: 12\r\nAccept: */*\r\n\r\nHello world!'
```

Uniquely, the `__str__` method returns the objects with arrows to make obvious of its type:

```python
print(req)
print(resp)
```

```
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
```
