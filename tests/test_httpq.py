import httpq
import pytest


class Test_Headers:
    def test_headers_init(self):
        httpq.Headers()

    def test_headers_raw(self):
        httpq.Headers({"hello": "world"}).raw


class Test_Request:
    def test_request_init(self):
        req = httpq.Request()
        assert req.state == httpq.state.TOP

        req = httpq.Request(method="GET", target="/", protocol="HTTP/1.1")
        print(req, req.state)
        assert req.state == httpq.state.HEADER

        req = httpq.Request(method="GET", target="/", protocol="HTTP/1.1", headers={"Hello": "World"})
        assert req.state == httpq.state.BODY

        req = httpq.Request(
            method="GET",
            target="/",
            protocol="HTTP/1.1",
            headers={"Hello": "World", "Ola": ["Mundo", "World"]},
            body="Hello world",
        )
        assert req.state == httpq.state.BODY

        with pytest.raises(ValueError):
            httpq.Request(method="GET")

    def test_request_parse(self):
        req = httpq.Request.parse(b"GET / HTTP/1.1\r\n\r\n")
        assert req.state == httpq.state.BODY

    def test_request_feed(self):
        req = httpq.Request()
        assert req.state == httpq.state.TOP
        req.feed(b"GET /get HTTP/1.1\r\n")
        assert req.state == httpq.state.HEADER
        req.feed(b"Host: httpbin.org\r\n")
        req.feed(b"Content-Length: 18\r\n")
        req.feed(b"Accept: application/json\r\n")
        req.feed(b"Accept: text/plain\r\n")
        assert req.state == httpq.state.HEADER
        req.feed(b"\r\n")
        assert req.state == httpq.state.BODY
        req.feed(b"Hello world!")
        assert req.state == httpq.state.BODY

        assert req.method == "GET"
        assert req.target == "/get"
        assert req.protocol == "HTTP/1.1"
        assert req.headers == {
            "Host": "httpbin.org",
            "Content-Length": 18,
            "Accept": ["application/json", "text/plain"],
        }
        assert req.body == "Hello world!"

        with pytest.raises(TypeError):
            req.feed("hello")

    def test_request_set(self):
        req = httpq.Request(
            method="GET",
            target="/",
            protocol="HTTP/1.1",
            headers={"Hello": "World", "Ola": ["Mundo", "World"]},
            body="Hello world",
        )
        assert req.method == "GET"
        req.method = "POST"
        assert req.method == "POST"
        req.headers["Hello"] = "Mundo"
        assert req.headers["Hello"] == "Mundo"

    def test_request_raw(self):
        req = httpq.Request(
            method="GET",
            target="/",
            protocol="HTTP/1.1",
            headers={"Hello": "World", "Ola": ["Mundo", "World"]},
            body="Hello world",
        )
        assert req.raw == b"GET / HTTP/1.1\r\nHello: World\r\nOla: Mundo, World\r\n\r\nHello world"

    def test_request_str(self):
        req = httpq.Request(
            method="GET",
            target="/",
            protocol="HTTP/1.1",
            headers={"Hello": "World", "Ola": ["Mundo", "World"]},
            body="Hello world",
        )
        assert req.__str__() == "→ GET / HTTP/1.1\r\n→ Hello: World\r\n→ Ola: Mundo, World\r\n→ \r\n→ Hello world"

    def test_request_eq(self):
        req1 = httpq.Request.parse(
            b"GET /get HTTP/1.1\r\n"
            b"Host: httpbin.org\r\n"
            b"Content-Length: 12\r\n"
            b"Accept: application/json, text/plain\r\n"
            b"\r\n"
            b"Hello world!"
        )

        req2 = httpq.Request.parse(
            b"GET /get HTTP/1.1\r\n"
            b"Host: httpbin.org\r\n"
            b"Content-Length: 12\r\n"
            b"Accept: application/json\r\n"
            b"Accept: text/plain\r\n"
            b"\r\n"
            b"Hello world!"
        )

        print(req1 == req2)


class Test_Response:
    # Test all of the same things as the request class
    def test_response_init(self):
        resp = httpq.Response()
        assert resp.state == httpq.state.TOP

        resp = httpq.Response(protocol="HTTP/1.1", status=200, reason="OK")
        assert resp.state == httpq.state.HEADER

        resp = httpq.Response(protocol="HTTP/1.1", status=200, reason="OK", headers={"Hello": "World"})
        assert resp.state == httpq.state.BODY

        resp = httpq.Response(
            protocol="HTTP/1.1",
            status=200,
            reason="OK",
            headers={"Hello": "World", "Mundo": ["Ola", "Hello"]},
            body="Hello world",
        )
        assert resp.state == httpq.state.BODY

        with pytest.raises(ValueError):
            httpq.Response(status=200)

    def test_response_parse(self):
        resp = httpq.Response.parse(b"HTTP/1.1 200 OK\r\n\r\n")
        assert resp.state == httpq.state.BODY

    def test_response_feed(self):
        resp = httpq.Response()
        assert resp.state == httpq.state.TOP
        resp.feed(b"HTTP/1.1 200 OK\r\n")
        assert resp.state == httpq.state.HEADER
        resp.feed(b"Content-Length: 18\r\n")
        resp.feed(b"Accept: application/json\r\n")
        resp.feed(b"Accept: text/plain\r\n")
        resp.feed(b"\r\n")
        assert resp.state == httpq.state.BODY
        resp.feed(b"Hello world!")
        assert resp.state == httpq.state.BODY

        assert resp.protocol == "HTTP/1.1"
        assert resp.status == 200
        assert resp.reason == "OK"
        assert resp.headers == {
            "Content-Length": 18,
            "Accept": ["application/json", "text/plain"],
        }
        assert resp.body == "Hello world!"

        with pytest.raises(TypeError):
            resp.feed("hello")

    def test_response_set(self):
        resp = httpq.Response(
            protocol="HTTP/1.1",
            status=200,
            reason="OK",
            headers={"Hello": "World"},
            body="Hello world",
        )
        assert resp.protocol == "HTTP/1.1"
        resp.protocol = "HTTP/1.0"
        assert resp.protocol == "HTTP/1.0"
        resp.headers["Hello"] = "Mundo"
        assert resp.headers["Hello"] == "Mundo"

    def test_response_raw(self):
        resp = httpq.Response(
            protocol="HTTP/1.1",
            status=200,
            reason="OK",
            headers={"Hello": "World", "Ola": ["Mundo", "World"]},
            body="Hello world",
        )
        assert resp.raw == b"HTTP/1.1 200 OK\r\nHello: World\r\nOla: Mundo, World\r\n\r\nHello world"

    def test_response_str(self):
        resp = httpq.Response(
            protocol="HTTP/1.1",
            status=200,
            reason="OK",
            headers={"Hello": "World", "Ola": ["Mundo", "World"]},
            body="Hello world",
        )
        assert resp.__str__() == "← HTTP/1.1 200 OK\r\n← Hello: World\r\n← Ola: Mundo, World\r\n← \r\n← Hello world"

    def test_response_eq(self):
        resp1 = httpq.Response.parse(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Length: 12\r\n"
            b"Accept: application/json, text/plain\r\n"
            b"\r\n"
            b"Hello world!"
        )

        resp2 = httpq.Response.parse(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Length: 12\r\n"
            b"Accept: application/json\r\n"
            b"Accept: text/plain\r\n"
            b"\r\n"
            b"Hello world!"
        )

        print(resp1 == resp2)
