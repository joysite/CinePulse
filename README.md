# **🎬 影脉 (CinePulse) | 数字导演工作站项目文档**

## **1\. 项目愿景**

影脉（CinePulse）是一款语义驱动的自动化短片生产系统。它旨在通过 AI Agent 协同，将模糊的故事创意（灵魂）转化为包含剧本分镜、审美纠偏生图、语音合成及动态字幕的完整短片，实现“剧本即视频”的创作流程。

## **2\. 系统架构 (Agentic Workflow)**

系统采用模块化架构，核心由四个关键 Agent 组成：

* **编剧 Agent (WriterAgent)**: 基于 DeepSeek 模型，负责将原始故事点子拆解为具有结构化的 JSON 分镜脚本（包含旁白与视觉描述）。  
* **美术 Agent (ArtistAgent)**: 整合智谱 CogView-3-Plus，结合全局审美预设（Style Bias）生成高审美一致性的分镜图片。  
* **配音 Agent (VoiceAgent)**: 负责将分镜旁白转化为高质量音频流（当前版本可选集成）。  
* **总成引擎 (VideoComposer)**: 基于 MoviePy 与 ImageMagick，负责物理咬合素材，处理呼吸感缩放、动态字幕叠加及成片渲染。

## **3\. 核心技术特征**

### **3.1 语义联动与审美纠偏**

系统不仅是简单的生图，通过 style\_bias 预设（如 8k resolution, shallow depth of field 等），确保了不同分镜之间视觉风格的连续性。

### **3.2 鲁棒的合成引擎**

VideoComposer 针对复杂的 Linux 环境进行了深度优化：

* **多版本兼容**: 自动探测 MoviePy 1.0 与 2.0+ 的参数命名差异（如 fontsize 与 font\_size）。  
* **环境自适应**: 自动定位系统中的 ImageMagick 二进制路径，解决跨平台部署痛点。  
* **动态字幕渲染**: 采用 caption 模式，支持长文本自动换行与居中对齐。

## **4\. 关键问题解决记录 (Debug Logs)**

在开发过程中，针对“字幕无法显示”这一核心痛点进行了深度攻克，总结如下：

### **问题 A：ImageMagick 权限限制**

* **原因**: Linux 系统出于安全考虑，默认禁止 ImageMagick 处理文本渲染。  
* **方案**: 修改 /etc/ImageMagick-6/policy.xml，将 @\* 模式的 rights 由 none 改为 read|write。

### **问题 B：路径大小写敏感性 (Case Sensitivity)**

* **原因**: 配置文件 config.yaml 中使用 simhei.ttf，而物理文件名为 SimHei.ttf。Linux 环境下导致字体加载失败，触发静默回退逻辑。  
* **方案**: 修正配置文件路径，并在 VideoComposer 初始化时增加 os.path.exists 物理校验。

### **问题 C：字幕渲染区域异常**

* **原因**: MoviePy 在 method='caption' 下若不指定高度，有时会生成高度为 0 的透明图层。  
* **方案**: 在 text\_kwargs 中显式指定字幕高度（如 img\_clip.h \* 0.2），确保图层物理可见。

## **5\. 快速开始**

### **5.1 环境配置**

1. 安装依赖：pip install streamlit moviepy openai Pillow requests  
2. 安装系统级组件：sudo apt-get install imagemagick ghostscript  
3. 配置 assets/ 目录，确保包含支持中文的字体文件（如 SimHei.ttf）。

### **5.2 配置文件 (config.yaml)**

api\_keys:  
  deepseek: "YOUR\_KEY"  
  zhipu\_ai: "YOUR\_KEY"  
aesthetic:  
  style\_bias: "Cinematic lighting, 8k resolution, shallow depth of field"  
  font\_path: "assets/SimHei.ttf"

### **5.3 运行**

执行 streamlit run app.py --server.headless=true --server.address=0.0.0.0 --server.port=8501 即可进入导演控制台。

## **6\. 后续迭代方向**

* \[ \] **多角色音色匹配**: 根据剧本角色自动切换 Voice Agent 音色。  
* \[ \] **运镜指令化**: 引入更复杂的 MoviePy 变换，实现推拉摇移的模拟。  
* \[ \] **云端持久化**: 接入 Firestore 实现多端同步与多人协作制片。

*文档生成于：2024年4月 | CinePulse 开发组*
