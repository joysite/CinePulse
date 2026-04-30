import streamlit as st

class VisualEngine:
    @staticmethod
    def show_semantic_feedback(analysis):
        """在 UI 上展示语义联动反馈"""
        st.markdown(f"""
        <div style="padding:10px; border-radius:5px; background-color:{analysis['color_hex']}44; border-left:5px solid {analysis['color_hex']}">
            <b>审美律动：</b> 氛围 {analysis['mood']} | 灯光 {analysis['lighting']}
        </div>
        """, unsafe_allow_html=True)