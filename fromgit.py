"""
To use, do the following in one terminal:
  $ python sendreceive.py consume
 
and then in another terminal, do this:
  $ python sendreceive.py produce
 
This was taken from an example in the Kombu source tree that was spread across
multiple files. In order to compare and contrast easily with other messaging
pattern examples, the separate files were combined into a single one.
 
Original location:
  https://github.com/celery/kombu/tree/master/examples/simple_task_queue
"""
import sys
 
from kombu import Connection, Exchange, Queue
from kombu.common import maybe_declare
from kombu.mixins import ConsumerMixin
from kombu.pools import producers
from kombu.utils import kwdict, reprcall
from kombu.utils.debug import setup_logging
 
 
connection_string = "amqp://guest:guest@localhost:5672//"
priority_to_routing_key = {'high': 'hipri',
                           'mid': 'midpri',
                           'low': 'lopri'}
task_exchange = Exchange('tasks', type='direct')
task_queues = [Queue('hipri', task_exchange, routing_key='hipri'),
               Queue('midpri', task_exchange, routing_key='midpri'),
               Queue('lopri', task_exchange, routing_key='lopri')]
 
 
def hello_task(who="world"):
    print("Hello %s" % (who, ))
 
 
def send_as_task(connection, fun, args=(), kwargs={}, priority='mid'):
    payload = {'fun': fun, 'args': args, 'kwargs': kwargs}
    routing_key = priority_to_routing_key[priority]
    with producers[connection].acquire(block=True) as producer:
        maybe_declare(task_exchange, producer.channel)
        producer.publish(
            payload, serializer='pickle', compression='bzip2',
            routing_key=routing_key)
 
 
def run_producer():
    print "Connecting ..."
    with Connection(connection_string) as conn:
        print "Connected."
        print "Sending tasks ..."
        send_as_task(
            conn, fun=hello_task, args=('Kombu', ), kwargs={}, priority='high')
 
 
class Worker(ConsumerMixin):
 
    def __init__(self, connection):
        self.connection = connection
 
    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=task_queues,
                         callbacks=[self.process_task])]
 
    def process_task(self, body, message):
        fun = body['fun']
        args = body['args']
        kwargs = body['kwargs']
        self.info('Got task: %s', reprcall(fun.__name__, args, kwargs))
        try:
            fun(*args, **kwdict(kwargs))
        except Exception, exc:
            self.error('task raised exception: %r', exc)
        message.ack()
 
 
def run_consumer():
    setup_logging(loglevel='INFO')
    print "Connecting ..."
    with Connection(connection_string) as conn:
        print "Connected."
        print "Awaiting tasks ..."
        try:
            Worker(conn).run()
        except KeyboardInterrupt:
            print('kthnxbye')
 
 
if __name__ == "__main__":
    if sys.argv[0].startswith("python"):
        option_index = 2
    else:
        option_index = 1
    option = sys.argv[option_index]
    if option == "produce":
        run_producer()
    elif option == "consume":
        run_consumer()
    else:
        print "Unknown option '%s'; exiting ..." % option
        sys.exit(1)