import requests
import base64

class VoiceAgent:
    def __init__(self, api_key):
        self.api_key = api_key

    def generate_audio(self, text, save_path):
        """智谱 GLM-TTS 音频合成"""
        url = "https://open.bigmodel.cn/api/paas/v4/audio/speech"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": "glm-tts",
            "input": text,
            "voice": "longxiaochun",  # 可选: alloy, echo, fable, onyx, nova, shimmer
            "response_format": "wav"
        }
        
        
        try:
            print(f"Voice API Request: URL={url}, text_length={len(text)}")
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            
            print(f"Voice API Response: status={resp.status_code}, content_length={len(resp.content)}")
            
            if resp.status_code == 200:
                # 检查响应内容是否为空
                if not resp.content:
                    print("Voice Error: Empty response content")
                    return None
                
                # 检查是否为有效的音频数据
                if len(resp.content) < 100:  # 音频文件应该大于100字节
                    print(f"Voice Error: Response too small, possibly error message: {resp.content[:200]}")
                    return None
                
                with open(save_path, "wb") as f:
                    f.write(resp.content)
                print(f"Voice Success: Audio saved to {save_path}, size={len(resp.content)} bytes")
                return save_path
            else:
                # 尝试解析错误响应
                try:
                    error_data = resp.json()
                    print(f"Voice API Error: HTTP {resp.status_code}, Error: {error_data}")
                except:
                    print(f"Voice API Error: HTTP {resp.status_code}, Response: {resp.text[:500]}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Voice Network Error: {e}")
            return None
        except Exception as e:
            print(f"Voice Error: {e}")
            return None