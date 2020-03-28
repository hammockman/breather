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
            topics.append( (topic, 0) )
            self.messages[topic] = default_value # ensure every topic of interest has an initial value # FIXME: on RECONNECT we want to resume prev value not overwrite!!!
        #print(topics)
        #import pdb; pdb.set_trace()
        client.subscribe(topics) # more efficient than subscribing one-topic-at-a-time apparently

        
    def on_message(self, client, userdata, msg):
        """
        Callback used for messages not dealt with by a topic specific handler
        """
        print(msg.topic+": "+msg.payload)
        self.messages_recv += 1
        self.messages[msg.topic] = msg.payload


    def __init__(self, subscribe_to_topics={}):
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
        self.messages_recv = 0
        self.messages = {}
        self.client.connect("localhost", 1883, 60)
        self.daemon = True  # set this to terminate when main program exits
        self.start()

        
    def run(self):
        self.client.loop_forever()


    def publish(self, topic, payload=None, qos=0, retain=False):
        self.client.publish(topic, payload, qos, retain)

if __name__=="__main__":
    T = MessagingThread()  # ^C can't kill this...
