import streamlit as st
from streamlit_carousel import carousel
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
import base64

def autoplay_audio_html(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    html = f"""
    <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """
    st.markdown(html, unsafe_allow_html=True)

load_dotenv()

GEM_K = os.getenv("GKEY")

client = genai.Client(api_key=GEM_K)

with open('data/exps.json', 'r') as f:
    exps = json.load(f)

if "page" not in st.session_state:
    st.session_state["page"] = "main"

if "sel_exp" not in st.session_state:
    st.session_state["sel_exp"] = None

if "last_exp" not in st.session_state:
    st.session_state["last_exp"] = None

if "msgs" not in st.session_state:
    st.session_state["msgs"] = []

if "audio_played" not in st.session_state:
    st.session_state["audio_played"] = False

if "from_qr" not in st.session_state:
    st.session_state["from_qr"] = False

query = st.query_params

if "exp" in query and query["exp"] in exps:
    st.session_state["sel_exp"] = query["exp"]
    st.session_state["page"] = f"details_{query['exp']}"
    st.session_state["from_qr"] = True
else:
    st.session_state["from_qr"] = False

current_exp = st.session_state["sel_exp"]

if current_exp is not None and st.session_state["last_exp"] != current_exp:
    st.session_state["msgs"] = []
    st.session_state["last_exp"] = current_exp
    st.session_state["audio_played"] = False

if st.session_state['page'] == 'main':
    st.set_page_config(layout="centered")
    st.title("POC AI Lab")
    st.write("Welcome to the POC AI Lab! Please select an experiment to view its details.")
    with st.container():
        for exp in exps.keys():
            with st.container(border=True):
                st.subheader(exps[exp]['apparatus'])
                for l in range(0,len(exps.keys())):
                    prods_list=[]
                    for i,j in enumerate(exps[exp]['images']):
                        prods_list.append({
                            "title":" ",
                            "text": " ",
                            "img": j,
                            "interval": None
                        })
                carousel(items=prods_list)
                
                if st.button(f"Details for {exp}",key=exp, use_container_width=True):
                    st.session_state['page']=f'details_{exp}'
                    st.session_state['sel_exp']=exp
                    st.rerun()

for exp in exps.keys():
    if st.session_state['page'] == f'details_{exp}':
        st.set_page_config(layout="wide")
        if st.button("Back"):
            st.session_state["page"] = "main"
            st.query_params.clear()
            st.rerun()
        
        prods_list=[]
        exp_id = st.session_state['sel_exp']
        st.title(exps[exp_id]['apparatus'])
        if st.session_state["from_qr"] and not st.session_state["audio_played"]:
                
                # 1️⃣ Best-effort autoplay (HTML hack)
                autoplay_audio_html(exps[exp_id]['audio_loc'])

                # 2️⃣ Visible fallback (always works)
                st.info("If audio does not start automatically, tap below 👇")
                if st.button("▶ Play Narration"):
                    st.audio(exps[exp_id]['audio_loc'])

                # Mark as attempted (prevents reruns)
                st.session_state["audio_played"] = True

        else:
            # Normal manual playback
            st.audio(exps[exp_id]['audio_loc'])
        c_1, c_2 = st.columns(2)
        with c_1:
            st.subheader(exps[exp_id]['apparatus'])
            for i, j in enumerate(exps[exp_id]['images']):
                prods_list.append({
                    "title": " ",
                    "text": " ",
                    "img": j,
                    "interval": None
                })
            carousel(items=prods_list)

            st.write(exps[exp_id]['narration_script'])

            # 🔊 AUDIO LOGIC WITH FAIL-SAFE
            

        with c_2:
            st.title("Experiment Details")

            if "msgs" not in st.session_state:
                st.session_state["msgs"] = []

            # ---- INPUT FIRST (capture & mutate state) ----
            prompt = st.chat_input("Ask any questions about this experiment")

            if prompt:
                st.session_state["msgs"].append({
                    "role": "user",
                    "content": prompt
                })

                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt
                    )
                    reply = response.text.strip()
                except Exception as e:
                    reply = f"⚠️ Error: {e}"

                st.session_state["msgs"].append({
                    "role": "assistant",
                    "content": reply
                })

                st.rerun()

            # ---- CHAT BOX SECOND (render-only) ----
            chat_box = st.container(border=True, height=450)
            with chat_box:
                for msg in st.session_state["msgs"]:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

