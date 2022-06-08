#####
httpq
#####

.. code-block:: python

    from httpq import Request, Response, state

.. automodule:: httpq.httpq

----

.. autoclass:: httpq.httpq.Headers
    :members:

----

.. autoclass:: httpq.httpq.Message
    :members:

----

.. autoclass:: httpq.httpq.Request
    :members:

.. autoclass:: httpq.httpq.Response
    :members:

----

.. autoclass:: httpq.httpq.state
    :members:

    * ``TOP``: Message is at the top line.
    * ``HEADERS``: Message is in the headers.
    * ``BODY``: Message is in the body.
