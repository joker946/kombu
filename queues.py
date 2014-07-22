from kombu import Exchange, Queue

task_exchange = Exchange('msgs', type='direct')
queue_array = [Queue('messages_1', task_exchange, routing_key = 'message_1'),
			   Queue('messages_2', task_exchange, routing_key = 'message_2')]