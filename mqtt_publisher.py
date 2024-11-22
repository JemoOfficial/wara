import os
import json
import time
import requests
import paho.mqtt.client as mqtt

# WooCommerce API-Details
wc_api_url = "https://172.18.0.5/wp-json/wc/v3/orders"
params = {
    'consumer_key': 'ck_43bcc2f523d9b319af2ca48f339a29c1e69bfa61',
    'consumer_secret': 'cs_7b8e21f94e6aba66bd4e96062140c62f08ac7aab'
}

# Funktion zur Abruf der Bestellungen
def get_orders():
    response = requests.get(wc_api_url, params=params, verify=False)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.json()

# MQTT-Einstellungen
mqtt_host = os.getenv('MQTT_HOST')
mqtt_port = int(os.getenv('MQTT_PORT', 1883))

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {rc}")

def on_log(client, userdata, level, buf):
    print(f"log: {buf}")

client = mqtt.Client(client_id="test_client")
client.on_connect = on_connect
client.on_log = on_log

try:
    print(f"Connecting to MQTT broker at {mqtt_host}:{mqtt_port}")
    client.connect(mqtt_host, mqtt_port, 60)
    client.loop_start()
except Exception as e:
    print(f"Connection failed: {e}")

while True:
    try:
        print("Sending request to WooCommerce API...")
        orders = get_orders()
        print("Received response from WooCommerce API")
        print(f"Retrieved {len(orders)} orders from WooCommerce")

        for order in orders:
            order_id = order['id']
            status = order['status']
            print(f"Order ID: {order_id}, Status: {status}")  # Debug-Ausgabe

            # Nur Bestellungen mit einem anderen Status als "completed" senden
            if status != "completed":
                try:
                    client.publish("order_json_mqtt_publish", json.dumps(order)) # wenn es nicht geht dann hier einfach "your topic name" löschen, wir mitgesendet...
                    print(f"Published data: {order}")

                    # Aktualisiere den Status der Bestellung auf "completed"
                    update_data = {
                        "status": "completed"
                    }
                    update_response = requests.put(f"https://172.18.0.5/wp-json/wc/v3/orders/{order_id}", json=update_data, params=params, verify=False)
                    if update_response.status_code == 200:
                        print(f"Updated order {order_id} to completed")
                    else:
                        print(f"Failed to update order {order_id}, response: {update_response.text}")

                except Exception as e:
                    print(f"Publishing failed: {e}")

    except Exception as e:
        print(f"Failed to retrieve or publish orders: {e}")

    time.sleep(10)
