import streamlit as st
from transformers import AutoModelForCausalLM, AutoTokenizer

# Hugging Face model and tokenizer
MODEL_PATH = st.secrets["MODEL_PATH"]
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH)

# App title
st.set_page_config(
    page_title="AI: Chatting...",
    page_icon=st.secrets["FAVICON"],
    layout="wide",
)
st.title("AI Chat Bot")
st.logo(
    st.secrets["LOGO"],
    icon_image=st.secrets["ICON"],
)
st.write('This chatbot is created using a fine-tuned GPT-2 model trained on sales data.')

# Store LLM generated responses
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Function for generating responses
def generate_response(prompt_input):

    # Include a detailed context in the prompt
    context = (
        "You are a data analysis assistant specializing in sales data for a supermarket in a hotel named Galaxy Inn, Athi River. "
        "Your responses should be relevant to sales data analysis, customer trends, "
        "and provide insightful information. Avoid providing unrelated information. "
        "Answer in a concise and professional manner.\n\n"
        "Example:\n"
        "User: Can you provide an analysis of our monthly sales trends?\n"
        "Assistant: Certainly! Based on the sales data from the past six months, we see a steady increase in sales volume, with a peak in December. The most popular product during this period was the Galaxy S4, accounting for 30% of total sales.\n\n"
        "User: "
    )
    
    # Concatenate the context with the user's input
    full_prompt = f"{context} {prompt_input} \nAssistant:"

    inputs = tokenizer(full_prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_length=200, num_return_sequences=1, no_repeat_ngram_size=2)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Remove the context part from the response
    response = response.replace(context, "").strip()
    response = response.replace(prompt_input, "").strip()
    
    return response

# User-provided prompt
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(prompt)
            st.write(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
