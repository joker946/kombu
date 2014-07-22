from __future__ import with_statement
from queues import task_exchange
from queues import queue_array
from kombu import Queue
from kombu.common import maybe_declare
from kombu.pools import producers
from kombu.mixins import ConsumerMixin

array_of_backstage_items = []

class P(ConsumerMixin):
    def __init__(self, connection):
        self.connection = connection
        return
    
    def get_consumers(self, Consumer, channel):
        return [Consumer( array_of_backstage_items, accept=['pickle'], callbacks = [ self.on_message ])]
    
    def on_message(self, body, message):
        print ("RECEIVED MSG - body: %r" % (body,))
        #print ("RECEIVED MSG - message: %r" % (message,))
        message.ack()
        return

if __name__ == "__main__":
    from kombu import BrokerConnection
    
    connection = BrokerConnection("amqp://guest:guest@localhost:5672//")

    with producers[connection].acquire(block=True) as producer:
        maybe_declare(task_exchange, producer.channel)
        
        array_of_backstage_items.append(Queue(queue_array[0].name+'_back', task_exchange,
         routing_key = queue_array[0].routing_key+'_back'))
        payload = {"type": "handshake", "content": "hello #1", "back": queue_array[0].routing_key+'_back'}
        producer.publish(payload, exchange = 'msgs', serializer="pickle", routing_key = 'message_1')

        array_of_backstage_items.append(Queue(queue_array[1].name+'_back', task_exchange,
         routing_key = queue_array[1].routing_key+'_back'))

        payload = {"type": "handshake", "content": "hello #2", "back": queue_array[1].routing_key+'_back'}
        producer.publish(payload, exchange = 'msgs', serializer="pickle", routing_key = 'message_2')
    with BrokerConnection("amqp://guest:guest@localhost:5672//") as connection:
    	try:
        	P(connection).run()
    	except KeyboardInterrupt:
        	print("bye bye")