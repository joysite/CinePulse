import streamlit as st
import yaml
import os
import time
import logging
from datetime import datetime
from database import WorkspaceDB
from agents.writer import WriterAgent
from agents.artist import ArtistAgent
from agents.voice import VoiceAgent
from utils.visual_engine import VisualEngine
from utils.video_composer import VideoComposer

# --- 0. 日志系统配置 ---
if not os.path.exists("logs"):
    os.makedirs("logs")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/cinepulse_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CinePulse-Core")

# --- 1. 配置加载与初始化 ---
@st.cache_resource
def init_system_resources():
    logger.info("正在初始化系统资源...")
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        db = WorkspaceDB()
        writer = WriterAgent(config['api_keys']['deepseek'])
        artist = ArtistAgent(config['api_keys']['zhipu_ai'], config['aesthetic']['style_bias'])
        voice = None  # 语音 Agent 暂不启用
        composer = VideoComposer(config['aesthetic']['font_path'])
        
        return config, db, writer, artist, voice, composer
    except Exception as e:
        st.error(f"❌ 系统启动失败: {e}")
        st.stop()

config, db, writer, artist, voice, composer = init_system_resources()

# 确保目录存在
for directory in ["workspace", "output", "logs"]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# --- 2. 页面配置 ---
st.set_page_config(page_title="影脉 CinePulse", layout="wide")

# --- 3. 侧边栏控制面板 ---
with st.sidebar:
    st.title("🎬 CinePulse")
    st.divider()
    
    st.subheader("📊 运行日志")
    log_placeholder = st.empty()
    
    if st.button("🧹 重置工作区"):
        db.clear_all()
        st.rerun()
    
    st.divider()
    st.subheader("🎥 导出选项")
    output_filename = st.text_input("成片文件名", value="masterpiece_v1.mp4")
    
    if st.button("🌟 启动影脉总成", width='stretch'):
        scenes = db.get_all_scenes()
        completed_scenes = [s for s in scenes if s[5] == 'COMPLETED']
        
        if not completed_scenes:
            st.error("当前没有已渲染完成的分镜片段。")
        else:
            with st.spinner("正在物理咬合所有影脉片段并渲染字幕..."):
                try:
                    all_clips = []
                    for s in completed_scenes:
                        # 核心调用：合成视频、音频与字幕
                        clip = composer.create_clip(s[3], s[4], s[1])
                        if clip: all_clips.append(clip)
                    
                    if all_clips:
                        # 确保产出保存到 output 文件夹
                        save_path = os.path.join("output", output_filename)
                        final_path = composer.save_movie(all_clips, save_path)
                        
                        st.success("🎥 成片渲染成功！")
                        # 前端预览
                        st.video(final_path)
                        
                        # 提供下载选项[cite: 2]
                        with open(final_path, "rb") as f:
                            st.download_button(
                                label="💾 下载成片",
                                data=f,
                                file_name=output_filename,
                                mime="video/mp4"
                            )
                        st.balloons()
                except Exception as e:
                    st.error(f"合成引擎异常: {e}")

# --- 4. 主工作流界面 ---
st.title("🎬 影脉 (CinePulse) | 数字导演工作站")
col_script, col_monitor = st.columns([0.6, 0.4])

with col_script:
    st.subheader("📝 剧本语义驱动")
    story_input = st.text_area("输入故事灵魂", height=120)
    
    if st.button("🔥 激活编剧 Agent", width='stretch'):
        if story_input:
            with st.spinner("构思中..."):
                script_data = writer.generate_storyboard(story_input)
                if 'scenes' in script_data:
                    db.clear_all()
                    for s in script_data['scenes']:
                        db.add_scene(s['narration'], s['visual_desc'])
                    st.rerun()

    st.divider()
    
    scenes = db.get_all_scenes()
    for s in scenes:
        scene_id, narration, v_desc, img_p, aud_p, status = s
        with st.container():
            st.markdown("<div class='pulse-card'>", unsafe_allow_html=True)
            st.write(f"**分镜 {scene_id}**")
            
            edited_narration = st.text_area(f"旁白", value=narration, key=f"n_{scene_id}")
            
            if st.button(f"🎬 锁定并渲染", key=f"btn_{scene_id}"):
                with st.spinner(f"正在生成素材..."):
                    try:
                        ts = int(time.time())
                        img_file = f"workspace/img_{scene_id}_{ts}.png"
                        
                        # 1. 生成图片
                        img_result = artist.generate_image(v_desc, img_file)
                        img_exists = img_result and os.path.exists(img_result)
                        
                        # 2. 检查图片有效性
                        if img_exists and os.path.getsize(img_result) > 1000:
                            # 3. 更新数据库：设置为 COMPLETED 状态，无音频模式传入空字符串[cite: 1]
                            db.update_scene_assets(scene_id, img_file, "", "COMPLETED")
                            st.toast(f"分镜 {scene_id} 渲染完成")
                        else:
                            db.update_scene_assets(scene_id, status="FAILED")
                            st.error(f"分镜 {scene_id} 图像生成失败")
                        st.rerun()
                    except Exception as e:
                        st.error(f"渲染失败: {e}")
            st.markdown("</div>", unsafe_allow_html=True)

with col_monitor:
    st.subheader("🎥 影脉监视器")
    if not scenes:
        st.info("等待主公落笔...")
    else:
        for s in scenes:
            scene_id, _, _, img_p, aud_p, status = s
            with st.expander(f"分镜 {scene_id}: {status}", expanded=(status == "COMPLETED")):
                if status == "COMPLETED" and img_p and os.path.exists(img_p):
                    st.image(img_p)
                elif status == "FAILED":
                    st.error("生成失败")

# 实时日志显示
try:
    with open(f"logs/cinepulse_{datetime.now().strftime('%Y%m%d')}.log", "r") as lf:
        log_placeholder.code("".join(lf.readlines()[-5:]))
except:
    pass