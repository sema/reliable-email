reliable-email
==============

This is my take on the **email service** presented by the Uber tool team's coding challenge[1].

Overview and Guarantees
-----------------------

The reliable-email service allows a *client* to submit emails to the *service*. The email will eventually be sent to its recipient(s) through one of many possible *backends*.  
The service is build with the following properties in mind.

 * Low latency: Clients should be able to submit emails to the service quickly and continue with their business.
 * High availability: Clients should not need/expect to buffer or retry submitting emails under normal circumstances, and emails should be sent to recipients even if single email services fail.
 * Stable client interface: Minimize the need of updating client facing interfaces and code. Many different clients will use this service, and we do not want to update them often.
 * Durability: When the client submits an email, then that email *will* eventually be sent to its recipient (if possible). We do not want data (email) loss.
 
The suggested architecture of reliable-email is as follows:
 
 client -> [HA] -> web frontend -> [redis cluster] <-> worker -> [external e-mail service]
  
A client submits emails to the web frontend through some HA layer, any standard solution for web services would work here (high availability).  
The web frontend exposes a stable and minimalistic interface through the HTTP protocol, to minimize the need of changing client code as reliable-email is evolved (stable client interface). 
If the web frontend responds with a success, then the client is guaranteed that the email will eventually be sent (if possible).

The web frontend persists emails in a redis cluster before returning with the success status code, guaranteeing emails are not lost (durability). 
Furthermore, decoupling email submission and sending (using redis as an intermediary) decreases latency for the clients (low latency) compared to immediately sending emails.

Finally, one or more workers process the queue of emails in the redis cluster, sending the emails using external email services. 
Using multiple email backends guards against isolated failures from email providers (high availability). 

In summary, reliable-email provides client libraries (```clients/```), the web frontend (```frontend/```), and workers (```workers/```). 

Web Frontend API (submitting emails)
------------------------------------

The Web Frontend exposes a single endpoint "/", accepting HTTP POST requests only.

The HTTP POST request must contain the following parameters:

    subject: The subject string
    body: The email body
    to: valid recipient email
    to_name (optional): name of the recipient
    from (optional): valid sender email
    from_name (optional): name of the sender
    
Default values for ``from`` and ``from_name`` can be configured for the web frontend.

The HTTP POST request is expected to return one of three status codes:

    200: Success
    400: Illformed submission
    500: Could not handle request (e.g. the redis cluster is down)
    
In addition, the Web Frontend will include a JSON formatted response, on the form:

```
{
  ok: 'false',
  error_message: 'message'
}
```

``ok`` is true on success and false on failure. If true the client is guaranteed that the submitted email will eventuall
 by sent. If false the supplied error message may give a reason.

A Python client and a web interface is supplied in ``clients/``. **The web interface is for development and debugging only**.

Worker API (processing emails)
------------------------------

TODO

About the Solution (Uber Coding challenge)
------------------------------------------

Selected track: Backend track (no or minimal frontend).

 * Implementation language: Python (experienced)
 * Web frontend framework: Flask (no prior experience)
 * Redis: (no prior experience)

 [1] https://github.com/uber/coding-challenge-tools/

