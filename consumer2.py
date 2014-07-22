from queues import queue_array
from kombu.mixins import ConsumerMixin
from kombu.pools import producers
from kombu.common import maybe_declare
from queues import task_exchange
import json
class C(ConsumerMixin):
    def __init__(self, connection):
        self.connection = connection
        return
    
    def get_consumers(self, Consumer, channel):
        
        return [Consumer( queue_array[1], accept=['pickle'], callbacks = [ self.on_message ])]
    
    def on_message(self, body, message):
        #print "get"
        print ("RECEIVED MSG - body: %r" % (body,))
        #print message.channel
        #print ("RECEIVED MSG - message: %r" % (message,))
        temp = body.get('back')
        message.ack()
        self.send_message_back(temp)
        return
    def send_message_back(self, message):
        with producers[connection].acquire(block=True) as producer:
            payload = {"header":"back-stage message2"}
            maybe_declare(task_exchange, producer.channel)
            producer.publish(payload, exchange = task_exchange, serializer="pickle", routing_key = message)

if __name__ == "__main__":
    from kombu import BrokerConnection
    from kombu.utils.debug import setup_logging
    
    setup_logging(loglevel="DEBUG")

    with BrokerConnection("amqp://guest:guest@localhost:5672//") as connection:
        try:
            C(connection).run()
        except KeyboardInterrupt:
            print("bye bye")