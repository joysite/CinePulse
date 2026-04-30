import os
import PIL.Image
import subprocess
import logging
from moviepy.config import change_settings

# 获取日志记录器
logger = logging.getLogger("CinePulse-Core")

# --- 1. 自动定位 ImageMagick ---
def find_imagemagick():
    try:
        res = subprocess.run(['which', 'convert'], capture_output=True, text=True)
        if res.returncode == 0:
            return res.stdout.strip()
    except:
        pass
    return "/usr/bin/convert" 

change_settings({"IMAGEMAGICK_BINARY": find_imagemagick()})

# --- 2. Pillow 兼容性 ---
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

# --- 3. MoviePy 多版本导入 ---
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
        :param font_path: 字体文件的相对或绝对路径
        """
        # 大小写与路径存在性校验
        if font_path:
            abs_path = os.path.abspath(font_path)
            if not os.path.exists(abs_path):
                # 如果找不到，尝试列出 assets 目录协助诊断
                assets_dir = os.path.dirname(abs_path)
                existing_files = os.listdir(assets_dir) if os.path.exists(assets_dir) else "目录不存在"
                logger.error(f"❌ 字体文件未找到: {font_path} (绝对路径: {abs_path})")
                logger.error(f"📂 当前 assets 目录下文件: {existing_files}")
                # 抛出异常防止后续静默失败
                raise FileNotFoundError(f"字体文件不存在，请检查 config.yaml 中的大小写: {font_path}")
            self.font_path = abs_path
        else:
            self.font_path = None
            logger.warning("⚠️ 未配置字体路径，字幕可能无法正常显示")

    def create_clip(self, img_path, aud_path, narration):
        if not img_path or not os.path.exists(img_path): 
            logger.error(f"❌ 图像素材不存在: {img_path}")
            return None
        
        try:
            # 1. 确定时长
            duration = 3.0
            audio = None
            if aud_path and os.path.exists(aud_path):
                audio = AudioFileClip(aud_path)
                duration = audio.duration
            
            # 2. 图像层
            img_clip = ImageClip(img_path)
            setter = "with_duration" if hasattr(img_clip, "with_duration") else "set_duration"
            img_clip = getattr(img_clip, setter)(duration)
            
            # 呼吸感缩放效果
            img_clip = img_clip.resize(lambda t: 1 + 0.04 * t)
            
            # 3. 字幕层
            text_kwargs = {
                "font": self.font_path,
                "color": 'white',
                "method": 'caption',
                "size": (img_clip.w * 0.8, img_clip.h * 0.2), # 显式高度
                "align": 'center'
            }
            
            # 自动探测版本参数名
            import inspect
            sig = inspect.signature(TextClip.__init__)
            if 'font_size' in sig.parameters:
                text_kwargs['font_size'] = 40
            else:
                text_kwargs['fontsize'] = 40

            # 渲染字幕
            txt_clip = TextClip(narration, **text_kwargs)
            
            # 设置字幕时长和位置
            txt_setter = "with_duration" if hasattr(txt_clip, "with_duration") else "set_duration"
            pos_setter = "with_position" if hasattr(txt_clip, "with_position") else "set_position"
            
            txt_clip = getattr(txt_clip, txt_setter)(duration)
            # 放在画面底部 80% 的位置
            txt_clip = getattr(txt_clip, pos_setter)(('center', img_clip.h * 0.8)) 
            
            # 4. 合成视频层
            video = CompositeVideoClip([img_clip, txt_clip])
            video = getattr(video, setter)(duration)
            
            # 5. 绑定音频
            if audio:
                aud_setter = "with_audio" if hasattr(video, "with_audio") else "set_audio"
                video = getattr(video, aud_setter)(audio)
                    
            return video
            
        except Exception as e:
            # 移除静默失败，直接打印错误
            logger.error(f"❌ 分镜 {img_path} 字幕渲染崩溃: {str(e)}")
            # 返回带渲染时长但无字幕的底层，保证视频不中断
            try:
                setter = "with_duration" if hasattr(img_clip, "with_duration") else "set_duration"
                return getattr(img_clip, setter)(duration)
            except:
                return None

    def save_movie(self, clips, output_path):
        valid_clips = [c for c in clips if c is not None]
        if not valid_clips:
            raise ValueError("没有有效的视频片段可以合成")
        
        # 使用 compose 方法确保字幕层被合并
        final = concatenate_videoclips(valid_clips, method="compose")
        final.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        return output_path