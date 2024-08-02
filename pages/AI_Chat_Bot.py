import streamlit as st
import torch
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer

st.set_page_config(
    page_title="AI: Chatting...",
    page_icon=st.secrets["FAVICON"],
    layout="wide",
)
# Hugging Face model and tokenizer
MODEL_PATH = st.secrets["MODEL_PATH"]

# Ensure the model path and all required files are present
try:
    load_in_4bit = True  # Adjust based on your setup

    # Load the model and tokenizer using peft
    model = AutoPeftModelForCausalLM.from_pretrained(
        MODEL_PATH,  # YOUR MODEL YOU USED FOR TRAINING
        load_in_4bit=load_in_4bit
    )
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
except Exception as e:
    st.error(f"Error loading model or tokenizer: {e}")

st.title("AI Chat Bot")
st.image(st.secrets["LOGO"], width=100)
st.write('This chatbot is created using a fine-tuned Alpaca trained Llama model trained on sales data.')

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

    # Prepare inputs and generate response
    inputs = tokenizer([full_prompt], return_tensors="pt")
    if torch.cuda.is_available():
        inputs = inputs.to("cuda")
        model = model.to("cuda")
    outputs = model.generate(**inputs, max_new_tokens=64, use_cache=True)
    response = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
    
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
