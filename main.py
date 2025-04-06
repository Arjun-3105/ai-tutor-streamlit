import streamlit as st
from together import Together
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set up Together client
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

# Streamlit setup
st.set_page_config(page_title="🧠 DeepSeek STEM Tutor", layout="centered")
st.title("📘 AI STEM Tutor with DeepSeek")
st.markdown("Ask your STEM questions like 'Integrate x', 'Explain Derivative', or 'Plot sin(x)'")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "memory_summary" not in st.session_state:
    st.session_state.memory_summary = None

# Clear memory option
if st.button("🧹 Clear Chat Memory"):
    st.session_state.messages = []
    st.session_state.memory_summary = None
    st.success("Memory cleared.")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_prompt = st.chat_input("Ask your STEM question...")

if user_prompt:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Summarize old messages if too long
    if len(st.session_state.messages) > 20 and st.session_state.memory_summary is None:
        with st.spinner("Summarizing memory..."):
            old_msgs = [m["content"] for m in st.session_state.messages[:-10] if m["role"] == "user" or m["role"] == "assistant"]
            full_text = "\n".join(old_msgs)

            summary_prompt = f"Summarize the following conversation for future context:\n\n{full_text}"
            try:
                summary_response = client.chat.completions.create(
                    model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
                    messages=[{"role": "user", "content": summary_prompt}]
                )
                summary = summary_response.choices[0].message.content
                st.session_state.memory_summary = summary
            except Exception as e:
                st.warning(f"Memory summarization failed: {e}")

    # Build prompt for current completion
    history = st.session_state.messages[-10:]
    context_msgs = []
    if st.session_state.memory_summary:
        context_msgs.append({"role": "system", "content": f"Here is a summary of earlier conversation: {st.session_state.memory_summary}"})

    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = client.chat.completions.create(
                    model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
                    messages=context_msgs + history + [{"role": "user", "content": user_prompt}]
                )
                bot_reply = response.choices[0].message.content
            except Exception as e:
                bot_reply = f"❌ Error: {e}"

        st.session_state.messages.append({"role": "assistant", "content": bot_reply})

        # Display response with proper LaTeX formatting
        for line in bot_reply.split("\n"):
            line = line.strip()
            if any(sym in line for sym in ["\\frac", "\\int", "\\sum", "^", "_", "\\sqrt", "\\boxed", "\\begin", "\\end"]):
                try:
                    st.latex(line)
                except:
                    st.markdown(line)
            else:
                st.markdown(line)
