"""
MQTT messaging for Ventilator control and UI

jh, Mar 2020
"""
import paho.mqtt.client as mqtt
import threading
import logging


class MessagingThread(threading.Thread):
    

    def on_message_runstate(self, client, userdata, msg):
        val = msg.payload.decode('utf-8')
        if val in ('run', 'pause', 'quit'):
            self.messages['breathe/runstate'] = val
        else:
            logging.error('unknown value for breathe/runstate: %s', val)


    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        assert rc==0
        topics = []
        for topic, (default_value, _) in self.subscribe_to_topics.items():
            topics.append( (topic, 0) ) # (topic, qos)
            self.messages[topic] = default_value # ensure every topic of interest has an initial value # FIXME: on RECONNECT we want to resume prev value not overwrite!!!
        #print(topics)
        #import pdb; pdb.set_trace()
        client.subscribe(topics) # more efficient than subscribing one-topic-at-a-time apparently

        
    def on_message(self, client, userdata, msg):
        """
        Callback used for messages not dealt with by a topic specific handler
        """
        #print(msg)
        try:
            content = msg.payload.decode('utf-8') # arrives as bytes
        except:
            content = msg.payload
        print(msg.topic+": "+content)
        self.messages_recv += 1
        self.messages[msg.topic] = content


    def __init__(self, subscribe_to_topics={}, daemon=True):
        threading.Thread.__init__(self)
        self.subscribe_to_topics = subscribe_to_topics
        self.client = mqtt.Client(client_id="breathe.manawa-ora.org", clean_session=False, transport="tcp")
        self.client.on_connect = self.on_connect
        #self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        #self.client.on_publish = self.on_publish
        for topic, (_, callback_name) in subscribe_to_topics.items():
            if callback_name is not None:
                self.client.message_callback_add(topic, getattr(self, 'on_message_'+callback_name))
            else:
                self.client.message_callback_add(topic, self.on_message)
        self.messages_recv = 0
        self.messages = {}
        #self.client.connect("localhost", 1883, 60)
        self.client.connect("manawa-ora-1", 1883, 60)
        self.daemon = daemon  # set this to terminate when main program exits
        self.start()

        
    def run(self):
        self.client.loop_forever()


    def publish(self, topic, payload=None, qos=0, retain=False):
        self.client.publish(topic, payload, qos, retain)

if __name__=="__main__":

    subscribe_to_topics = {
    # topic: (default_value, on_message_callback_function_name)
    'breathe/runstate': ('run', 'runstate'), # run, pause, quit
    #'breathe/runmode': ('AC', None), # AC=CMV, PC, ...
    #'breathe/inputs/fio2': (0.5, None), # fraction inspired oxygen 
    #'breathe/inputs/tv': (550, None), # ml; tidal volume
    'breathe/inputs/bpm': (8, None), # min^-1; backup breathing rate
    'breathe/inputs/inp': (20, None), # cmH20; inspiration pressure
    'breathe/inputs/peep': (2, None), # cmH20; positive end expiratory pressure
    'breathe/inputs/ieratio': (1, None), # ins:exp-iration ratio
    'breathe/inputs/patrigmode': (1, None), # can the patient trigger inspiration?
}
    T = MessagingThread(subscribe_to_topics, daemon=False)  # ^C can't kill this...
