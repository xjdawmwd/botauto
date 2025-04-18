import requests

class AllegroMessenger:
    def __init__(self, access_token):
        self.api_url = "https://api.allegro.pl/messaging/messages"
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/vnd.allegro.public.v1+json'
        }

    def send_message(self, order_id, text):
        data = {
            "recipient": {"login": f"order:{order_id}"},
            "text": text,
            "type": "ORDER_RELATED"
        }
        response = requests.post(self.api_url, json=data, headers=self.headers)
        return response.status_code == 201
