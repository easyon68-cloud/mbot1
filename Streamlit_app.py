# ...existing code...
import streamlit as st
import traceback

# Try to support both the new OpenAI client and the legacy openai package
try:
    from openai import OpenAI as OpenAIClient  # new SDK
    def make_client(key: str):
        return OpenAIClient(api_key=key)

    def extract_text_from_response(resp):
        # Try several common shapes
        try:
            return resp.choices[0].message.content
        except Exception:
            try:
                return resp['choices'][0]['message']['content']
            except Exception:
                try:
                    return resp.choices[0].text
                except Exception:
                    return str(resp)
    def create_chat_completion(client, messages, model="gpt-3.5-turbo"):
        return extract_text_from_response(client.chat.completions.create(model=model, messages=messages))
except Exception:
    import openai as legacy_openai  # legacy SDK
    def make_client(key: str):
        legacy_openai.api_key = key
        return legacy_openai

    def extract_text_from_response(resp):
        try:
            return resp['choices'][0]['message']['content']
        except Exception:
            try:
                return resp['choices'][0]['text']
            except Exception:
                return str(resp)
    def create_chat_completion(client, messages, model="gpt-3.5-turbo"):
        resp = client.ChatCompletion.create(model=model, messages=messages)
        return extract_text_from_response(resp)

# Ensure API key exists
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI key not found in Streamlit secrets (create .streamlit/secrets.toml with OPENAI_API_KEY).")
    st.stop()

client = make_client(api_key)

# Set the app title
st.title("🛠️ Network and Server Troubleshoot")

# Initialize chat history with a system prompt
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are a professional AI assistant specialized in network and server troubleshooting. "
                "Your role is to help users diagnose common issues related to connectivity, server performance, configuration errors, and system logs. "
                "You must clearly state that you are not a certified technician and do not provide emergency IT support. "
                "If a user asks about anything unrelated to IT troubleshooting, reply: "
                "'I'm here to help with network and server troubleshooting. Please ask about connectivity issues, server errors, or system configurations.' "
                "If a user describes critical infrastructure failure or data breach, respond: "
                "'This may indicate a serious issue. Please contact your IT department or cybersecurity team immediately.'"
            )
        }
    ]

# Display previous messages (excluding system prompt)
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# File upload section
uploaded_file = st.file_uploader("📁 Upload a log file for analysis", type=["txt", "log", "csv"])
if uploaded_file:
    try:
        file_bytes = uploaded_file.read()
        try:
            file_content = file_bytes.decode("utf-8")
        except Exception:
            file_content = file_bytes.decode("latin-1")
    except Exception:
        file_content = "<unable to read file>"

    st.text_area("📄 Log File Content", file_content, height=200)

    # Ask GPT to summarize the log
    summary_prompt = f"Please analyze and summarize the following troubleshooting log:\n\n{file_content}"
    try:
        summary_text = create_chat_completion(
            client,
            [
                {"role": "system", "content": "You are a helpful assistant that analyzes server and network logs."},
                {"role": "user", "content": summary_prompt}
            ],
            model="gpt-3.5-turbo",
        )
        st.subheader("🧾 Log Summary")
        st.write(summary_text)
    except Exception:
        st.error("Error calling OpenAI API for log summary.")
        st.text(traceback.format_exc())

# Chat input
user_input = st.chat_input("Describe your network or server issue...")

# Function to get AI response
def get_response(messages):
    try:
        return create_chat_completion(client, messages, model="gpt-3.5-turbo")
    except Exception:
        st.error("Error calling OpenAI API for chat response.")
        st.text(traceback.format_exc())
        return "An error occurred while contacting the AI service."

# Handle user input
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    response = get_response(st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)

# Footer disclaimer
st.markdown("---")
st.markdown(
    "⚠️ **Disclaimer:** This chatbot does not provide certified IT support or emergency services. "
    "Always consult your IT administrator or support team for critical infrastructure issues.",
    unsafe_allow_html=True
)
