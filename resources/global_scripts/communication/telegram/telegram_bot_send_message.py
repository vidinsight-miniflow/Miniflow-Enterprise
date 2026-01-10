"""
Telegram Bot Script: Mesaj gönderme
"""
import requests

def module():
    class TelegramBot:
        def run(self, params):
            """
            Args:
                params: {
                    "token": str,
                    "chat_id": str,
                    "text": str
                }
            Returns:
                {
                    "text": str,
                    "message_id": int
                }
            """
            token = params.get("token")
            chat_id = params.get("chat_id")
            text = params.get("text")
            
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text
            }
            
            response = requests.post(url=url, json=data)
            result = response.json()
            
            if result.get("ok") is not True:
                raise Exception(result.get("description", "Bilinmeyen bir hata oluştu"))
            
            return {
                "response": result
            }
    
    return TelegramBot()