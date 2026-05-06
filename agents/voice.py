import requests

class VoiceAgent:
    def __init__(self, api_key):
        self.api_key = api_key
        # API 服务器地址
        self.url = "https://open.bigmodel.cn/api/paas/v4/audio/speech"

    def generate_audio(self, text, save_path, voice="tongtong", speed=1.0, volume=1.0):
        """
        使用智谱 GLM-TTS 将文本转换为语音
        
        :param text: 要转换的文本内容 (最大 1024 字符)
        :param save_path: 音频保存路径
        :param voice: 音色选择 (tongtong, chuichui, xiaochen, jam, kazi, douji, luodo)
        :param speed: 语速 [0.5, 2]
        :param volume: 音量 (0, 10]
        """
        
        # 长度校验
        if len(text) > 1024:
            print(f"Voice Error: Input text too long ({len(text)} > 1024)")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 构造请求参数
        payload = {
            "model": "glm-tts",
            "input": text,
            "voice": voice,
            "speed": speed,
            "volume": volume,
            "response_format": "wav"  # 业务处理成功，采样率建议设置为 24000
        }

        try:
            print(f"Voice API Request: URL={self.url}, text_length={len(text)}")
            # 使用 POST 方法请求
            resp = requests.post(self.url, headers=headers, json=payload, timeout=30)
            
            # 处理 200 成功的响应
            if resp.status_code == 200:
                if not resp.content:
                    print("Voice Error: Empty response content")
                    return None
                
                # 直接保存二进制流数据
                with open(save_path, "wb") as f:
                    f.write(resp.content)
                print(f"Voice Success: Audio saved to {save_path}, size={len(resp.content)} bytes")
                return save_path
            
            else:
                # 处理请求失败，解析 Error Schema
                try:
                    error_data = resp.json()
                    err_info = error_data.get("error", {})
                    print(f"Voice API Error: Code={err_info.get('code')}, Message={err_info.get('message')}")
                except Exception:
                    print(f"Voice API Error: HTTP {resp.status_code}, Response: {resp.text[:500]}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Voice Network Error: {e}")
            return None
        except Exception as e:
            print(f"Voice Error: {e}")
            return None
