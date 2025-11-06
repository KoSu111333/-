import time
import json
import util
import paho.mqtt.client as mqtt
import time
import pickle

#logger = util.logging.getLogger("MyApp.MQTT") 


class MqttModule:
    """
    MQTT 통신을 관리하는 클래스
    """
    def __init__(self, bk_addr, bk_port, topics, client_id, if_cont):
        self.addr = bk_addr
        self.port = bk_port
        self.topics = topics
        self.client_id = client_id
        self.if_cont = if_cont
        self._is_connected = False
        self.mqtt_client = self._create_mqtt_client()
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._on_message

    def is_connected(self):
        return self._is_connected

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._is_connected = True
            for topic in self.topics:
                self.mqtt_client.subscribe(topic)
                print(f"[MQTT] 토픽 '{topic}' 구독 완료.")
                #logger.info(f"[MQTT] 토픽 '{topic}' 구독 완료.")
        else:
            self._is_connected = False
            #logger.exception(f"[MQTT] MQTT 연결 실패: Error Code {rc}")

    def _on_message(self, client, userdata, msg):
        try:
            if msg.topic == util.MQTT_TOPIC_RESPONSE_OCR:
                payload = msg.payload.decode('utf-8')
                parsed_data = json.loads(payload)
                final_payload = util.pack_payload(topic = util.MQTT_TOPIC_RESPONSE_OCR, payload = parsed_data)
                gate_id = parsed_data["gate_id"]
                
            elif msg.topic == util.MQTT_TOPIC_RESPONSE_FEE_INFO:
                payload = msg.payload.decode('utf-8')
                parsed_data = json.loads(payload)
                final_payload = util.pack_payload(topic = util.MQTT_TOPIC_RESPONSE_FEE_INFO, payload = parsed_data)
                gate_id = util.EXIT_GATE_ID
            elif msg.topic == util.MQTT_TOPIC_RESPONSE_AVAILABLE_COUNT:
                payload = msg.payload.decode('utf-8')
                parsed_data = json.loads(payload)
                final_payload = util.pack_payload(topic = util.MQTT_TOPIC_RESPONSE_AVAILABLE_COUNT, payload = parsed_data)
                gate_id = util.ENTRY_GATE_ID
                if util.EXIT_GATE_MODE:
                    gate_id = util.EXIT_GATE_ID
            else :
                final_payload = util.pack_payload(topic = None, payload = None)
            self.if_cont.notify_mqtt_msg(final_payload,gate_id) 
        except Exception as e:
            #logger.exception(f"[MQTT] MQTT 메시지 처리 오류: {e}")
            print(f"[MQTT] MQTT 메시지 처리 오류: {e}")
    def _create_mqtt_client(self):
        mqtt_client = mqtt.Client(client_id=self.client_id)
        return mqtt_client

    def connect_mqtt_broker(self, timeout=5):
        self.mqtt_client.connect(self.addr, self.port, 60)
        self.mqtt_client.loop_start()

        start_time = time.time()
        while not self._is_connected and time.time() - start_time < timeout:
            print("[MQTT] MQTT 연결 대기 중...")
            time.sleep(1)

        if not self._is_connected:
            #logger.exception(f"Error: {timeout}초 이내에 MQTT 브로커에 연결하지 못했습니다.")
            print("MQTT connection timeout")

            # raise RuntimeError("MQTT connection timeout")
            
    def mqtt_send_raw_data(self, topic,raw_data):
        json_data = json.dumps(raw_data)

        # print(f"[MQTT] MQTT 서버에 데이터 전송 시도: {json_data}...")

        result = self.mqtt_client.publish(topic, json_data, qos=1)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            # print("[MQTT] 데이터 전송 성공!")
            return True
        else:
            #logger.warning(f"[MQTT] MQTT 메시지 전송 실패: {result.rc}")
            return False

    def mqtt_publish(self, topic,paylaod):
        return self.mqtt_send_raw_data(topic,paylaod)

    def loop_stop(self):
        if self._is_connected:
            self.mqtt_client.loop_stop()

    def disconnect(self):
        if self._is_connected:
            self.mqtt_client.disconnect()
            #logger.warning(f"[MQTT] MQTT 브로커에서 연결을 끊었습니다.")

    def __str__(self):
        return (f"[MQTT][ADDR] : {self.addr}\n"
                f"[MQTT][PORT] : {self.port}\n"
                f"[MQTT][TOPIC] : {self.topics}\n"
                f"[MQTT][ID] : {self.client_id}\n")
