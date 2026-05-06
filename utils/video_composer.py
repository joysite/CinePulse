import os
import PIL.Image
import subprocess
import logging
from moviepy.config import change_settings

# 获取日志记录器
logger = logging.getLogger("CinePulse-Core")

# --- 1. 自动定位 ImageMagick (用于字幕渲染) ---
def find_imagemagick():
    try:
        res = subprocess.run(['which', 'convert'], capture_output=True, text=True)
        if res.returncode == 0:
            return res.stdout.strip()
    except:
        pass
    return "/usr/bin/convert" 

change_settings({"IMAGEMAGICK_BINARY": find_imagemagick()})

# --- 2. Pillow 兼容性处理 ---
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

# --- 3. MoviePy 多版本兼容导入 ---
try:
    from moviepy.editor import ImageClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
except ImportError:
    try:
        from moviepy import ImageClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
    except ImportError:
        from moviepy.video.VideoClip import ImageClip, TextClip
        from moviepy.audio.AudioClip import AudioFileClip
        from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
        from moviepy.video.compositing.concatenate import concatenate_videoclips

class VideoComposer:
    def __init__(self, font_path):
        """
        初始化合成器
        :param font_path: 字体文件的路径 (用于渲染分镜旁白字幕)
        """
        if font_path:
            abs_path = os.path.abspath(font_path)
            if not os.path.exists(abs_path):
                logger.error(f"❌ 字体文件未找到: {font_path}")
                raise FileNotFoundError(f"字体文件不存在: {font_path}")
            self.font_path = abs_path
        else:
            self.font_path = None
            logger.warning("⚠️ 未配置字体路径，字幕将使用系统默认字体")

    def create_clip(self, img_path, aud_path, narration):
        """
        核心逻辑：将图片、生成的语音、以及剧本旁白合成一个视频片段
        """
        if not img_path or not os.path.exists(img_path): 
            logger.error(f"❌ 图像素材不存在: {img_path}")
            return None
        
        try:
            # 1. 确定时长：优先读取语音 Agent 生成的音频时长
            audio = None
            if aud_path and os.path.exists(aud_path):
                audio = AudioFileClip(aud_path)
                duration = audio.duration
                logger.info(f"🔈 载入音频素材，时长: {duration:.2f}s")
            else:
                duration = 3.0  # 若无音频，默认停留 3 秒
                logger.warning(f"⚠️ 分镜 {img_path} 未找到有效音频，将使用默认时长")

            # 2. 图像层处理
            img_clip = ImageClip(img_path)
            # 兼容 moviepy v1/v2 的方法名[cite: 5]
            setter = "with_duration" if hasattr(img_clip, "with_duration") else "set_duration"
            img_clip = getattr(img_clip, setter)(duration)
            
            # 呼吸感缩放效果：赋予静态图像电影感[cite: 5]
            img_clip = img_clip.resize(lambda t: 1 + 0.04 * t)
            
            # 3. 字幕层配置
            text_kwargs = {
                "font": self.font_path,
                "color": 'white',
                "method": 'caption',
                "size": (img_clip.w * 0.8, None), # 宽度占 80%，高度自适应
                "align": 'center',
                "stroke_color": "black", # 添加描边增加可读性
                "stroke_width": 1
            }
            
            # 兼容性：检测 TextClip 初始化参数名
            import inspect
            sig = inspect.signature(TextClip.__init__)
            text_kwargs['font_size' if 'font_size' in sig.parameters else 'fontsize'] = 36

            # 渲染字幕并设置位置[cite: 3, 5]
            txt_clip = TextClip(narration, **text_kwargs)
            txt_setter = "with_duration" if hasattr(txt_clip, "with_duration") else "set_duration"
            pos_setter = "with_position" if hasattr(txt_clip, "with_position") else "set_position"
            
            txt_clip = getattr(txt_clip, txt_setter)(duration)
            # 字幕位于底部 85% 位置
            txt_clip = getattr(txt_clip, pos_setter)(('center', img_clip.h * 0.85)) 
            
            # 4. 物理合成层[cite: 3, 5]
            video = CompositeVideoClip([img_clip, txt_clip])
            video = getattr(video, setter)(duration)
            
            # 5. 绑定语音流[cite: 5, 6]
            if audio:
                aud_setter = "with_audio" if hasattr(video, "with_audio") else "set_audio"
                video = getattr(video, aud_setter)(audio)
                    
            return video
            
        except Exception as e:
            logger.error(f"❌ 分镜合成崩溃: {str(e)}")
            return None

    def save_movie(self, clips, output_path):
        """
        串联所有分镜片段并导出最终成片[cite: 5]
        """
        valid_clips = [c for c in clips if c is not None]
        if not valid_clips:
            raise ValueError("没有有效的视频片段可以合成")
        
        # method="compose" 确保字幕等图层被正确合并[cite: 3]
        final = concatenate_videoclips(valid_clips, method="compose")
        
        # 导出配置：libx264 编码，aac 音频编码[cite: 5]
        final.write_videofile(
            output_path, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True
        )
        return output_path
