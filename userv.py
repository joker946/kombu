import parsers.server as spars
from queues import add_queue
from queues import queues_dict
from qcow2.search_qcow import parse_dirs
from queues import task_exchange
from kombu.common import send_reply
from kombu.pools import producers
from kombu.mixins import ConsumerMixin


SNAME = spars.sname  # server name from terminal


class S(ConsumerMixin):
    def __init__(self, connection):
        self.connection = connection
        return

    def get_consumers(self, Consumer, channel):
        add_queue(SNAME, self.connection)

        return [Consumer(queues_dict[SNAME],
                accept=['json'],
                callbacks=[self.on_message])]

    def on_message(self, body, message):
        print("[X] Message catched.".upper())
        print ("BODY: %r" % (body,))
        message.ack()
        self.set_message(message=message, body=body)
        return

    def set_message(self, message, body):
            if body.get('kwargs'):
                folder = body.get('kwargs')['folder']
                qcow_info, _, _, _ = parse_dirs(folder)
            else:
                qcow_info, _, _, _ = parse_dirs()

            with producers[self.connection].acquire(block=True) as producer:
                #get producer from pool
                if qcow_info == []:
                    err_mess = "There are no qcow2 files in directory".upper()
                    send_reply(task_exchange, message,
                               err_mess, producer=producer)
                else:
                    send_reply(task_exchange, message,
                               qcow_info, producer=producer)
                print("[X] Reply message sent.".upper())
                print("---------------------------------")
            return

if __name__ == "__main__":
    from kombu import BrokerConnection
    #from kombu.utils.debug import setup_logging

    #setup_logging(loggers=['kombu'])

    with BrokerConnection("amqp://guest:guest@localhost:5672//") as connection:
        try:
            S(connection).run()
        except KeyboardInterrupt:
            print("bye bye")
