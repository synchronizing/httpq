# 🏃‍♂️ httpq

<p align="center">

  <a href="https://github.com/synchronizing/httpq/actions/workflows/pytest-cover-run.yaml">
    <img src="https://github.com/synchronizing/httpq/actions/workflows/pytest-cover-run.yaml/badge.svg">
  </a>

<a href="https://synchronizing.github.io/httpq/">
    <img src="https://github.com/synchronizing/httpq/actions/workflows/docs-publish.yaml/badge.svg">
  </a>
  
  <a href="https://coveralls.io/github/synchronizing/httpq?branch=master">
    <img src="https://coveralls.io/repos/github/synchronizing/httpq/badge.svg?branch=master">
  </a>

  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg">
  </a>
</p>

A module to parse, modify, and compile HTTP/1.1 messages with a simple built-in state machine.

## Installing

```
pip install httpq
```

## Documentation

Documentation can be found [here](https://synchronizing.github.io/httpq/).

## Using

`httpq` has three methods to initialize a `httpq.Request` and `httpq.Response` object.

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
    b"GET /get HTTP/1.1\r\n"
    b"Host: httpbin.org\r\n"
    b"Content-Length: 12\r\n"
    b"\r\n"
    b"Hello world!"
)

resp = httpq.Response.parse(
    b"HTTP/1.1 200 OK\r\n"
    b"Content-Length: 12\r\n"
    b"\r\n"
    b"Hello world!"
)
```

#### `feed`

```python
req = httpq.Request()
req.feed(b"GET /get HTTP/1.1\r\n")
req.feed(b"Host: httpbin.org\r\n")
req.feed(b"Content-Length: 18\r\n")
req.feed(b"\r\n")
req.feed(b"Hello world!")

resp = httpq.Response()
resp.feed(b"HTTP/1.1 200 OK\r\n")
resp.feed(b"Content-Length: 12\r\n")
resp.feed(b"\r\n")
resp.feed(b"Hello world!")
```

The feed mechanism comes with a simple built-in state machine. The state machine can be three states:

* `TOP`: The feed cursor is at the top of the message.
* `HEADER`: The feed cursor is at the headers.
* `BODY`: The feed cursor is at the body.

Once at the body it's the user's responsibility to keep track of the message length.

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

# At this stage we have a response that has read the top line, and the headers.
# With this, we can figure out the length of the body. In this case, using Content-Length.
length = resp.headers["Content-Length"]
```

Note that the feed mechanism is used in conjunction with the `step_state` method. This allows the state machine to be stepped through and the parser to be advanced. We can use this parse until the body of the message, and then use the captured headers to parse the body.

### Modifying and Comparisons

`httpq` also comes with an intuitive method to modify and compare message values:

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

Once the object is modified to the user's preference utilizing the `Request` and `Response` object is as easy as calling a property (specifically `.raw`):

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

Checkout the documentation for more details.
