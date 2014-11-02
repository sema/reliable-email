reliable-email
==============

This is my take on the **email service** presented by the Uber tool team's coding challenge[1].

Overview and Guarantees
-----------------------

The reliable-email service allows a *client* to submit emails to the *service*. The email will eventually be sent to its recipient(s) through one of many possible *backends*.  
The service is build with the following properties in mind.

 * Low latency: Clients should be able to submit emails to the service quickly and continue with their business. Emails are sent using backend services asynchronously.
 * High availability: Individual components are build to be run in clusters, such that 
   (1) clients can reasonably expect to submit their emails, we do not want email to accumulate at clients, and
   (2) clients can expect email to be delivered in a timely fashion, even if a single backend fails.
 * Stable client interface: Minimize the need of updating client facing interfaces and code. Many different clients will use this service, and we do not want to update them often.
 * Durability: When the client submits an email, then that email *will* eventually be sent to its recipient (if possible)*. We do not want data (email) loss.
 
The suggested architecture of reliable-email is as follows:
 
 client -> [HA] -> web frontend -> [redis cluster] <-> worker -> [external e-mail service]

*A client* can submit emails to reliable-email through the *web frontend*, which accepts simple POST requests. 
The web frontend is kept simple and the intention is to not change the interface which breaks old clients.
If the web frontend responds with a success, then the submitted email is guaranteed to eventually be sent (if possible)*. 

Submitted emails are persisted in a redis cluster, for which the web frontend acts as a producer and multiple workers act as consumers. 
Each worker polls redis for submitted emails, and sends the emails using configurable backends (AWS and sendgrid are currently supported).

The web frontend and workers are build to be stateless, and support many instances. The intention is to have multiple web frontends behind some
HA layer, to minimize the risk of the frontend being unavailable, and to use multiple workers using different backends, to handle individual backend failures.

Further, decoupling email submission and sending (using redis as an intermediary) decreases latency for the clients (low latency) compared to immediately sending emails.

In summary, reliable-email provides client libraries (```clients/```), a web frontend (```frontend/```), workers (```workers/```), and a CLI interface to inspect and manage the queue in redis (```cli/```).

*See open issues.

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

A base worker handles all interaction with the queue (redis), while delegating the act of sending emails to a backend. 
Backends (see ```workers/reworker/workers for inspiration```) must implement the following interface:
 
```
class SomeBackend(object):
  def __init__(self):
      pass
  
  def send(self, **kwargs):
      """
      Required kwargs
      
      subject: string:
      body: string:
      
      to_email: string: valid email of recipient
      to_name: string|None: name of recipient (optional)
      
      from_email: string: valid email of sender
      from_name: string|None: name of recipient (optional)
      
      connection_timeout: int|None: Global setting, timeout in seconds when retrying connections. None for no timeout, 0 for unlimited.
      connection_timeout_interval: int: Suggested polling interval between connection retries.
      
      """
      pass
```

Optinal values may not exist in the passed kwargs. 
An implementation of a backend should use ```**kwargs```, as new arguments may be added in the future.

If the worker returns, it is assumed that the email has been sent successfully. 
If the backend raises an WorkerInvalidEmail exception, then the passed email is discarded to the invalid email queue for later processing.
Any other exception is logged and and causes the worker to exit (it is expected that an external system restarts the worker).

The worker is expected to retry any failed connections, using ```connection_timeout``` and ```connection_timeout_interval``` as guides.
A decorator exists which implements a basic retry loop. See ```workers/reworker/workers/aws.py``` for an example. 

Persistence
-----------

Reliable-email relies on a redis instance, and expects data in redis to be persistent. Proper configuration of redis is an exercise left to the user.

The web frontend and worker communicates through three queues (lists) in redis, a work queue, a processing queue, and a discarded queue.
  Initially, an email is added to the work queue, which is polled by worker processes. 
  A worker selects an email by (atomically) moving the email from the work queue to a processing queue. When the worker has sent the email, then the email is removed from the processing queue.
  If the worker crashes, the email is still persisted, and can be returned to the work queue at some point.
  If the worker is unable to send the email, because the email is illformed, then the email is moved to a discard queue for later processing.
  
Notice, that the above ensures that no email is lost before it is sent. However, it is possible for an email to be sent twice 
(e.g. if moved to the processing queue, sent, but never removed because the worker is killed). 

Open Issues / TODOs
-------------------

Email Validation
^^^^^^^^^^^^^^^^

Some initial email validation is conducted in the web frontend, while the worker and individual worker backends apply final validation of the submitted email.
 Thus, an illformed email can be rejected even though its submission was initially accepted. 
 This causes emails to be discarded from the queue, and moved to a discard queue for later processing.
 
An alternative solution would be to apply all validation in the web frontend, and reject any illformed emails immediately. 
However, there will always be the possibility that a email is rejected from the external service, so it is not possible to avoid supporting a path where emails are
  rejected by the workers.

Dropped Emails in Processing Queue
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Workers move emails from the main mail queue to a temporary *processing queue*, such that if the worker is killed while processing an email, the email is still persisted.
However, these emails are never *recovered* (put back into the main queue). A process is needed to identify such emails and recover them.

About the Solution (Uber Coding challenge)
------------------------------------------

Selected track: Backend track (no or minimal frontend).

 * Implementation language: Python (experienced)
 * Web frontend framework: Flask (no prior experience)
 * Redis: (no prior experience)

 [1] https://github.com/uber/coding-challenge-tools/

