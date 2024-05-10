import gradio as gr

def yes_man(message, history):
    if message.endswith("?"):
        return "Yes"
    else:
        return "Ask me anything!"

gr.ChatInterface(
    yes_man,
    chatbot=gr.Chatbot(height=300),
    textbox=gr.Textbox(placeholder="What is your question", container=False, scale=7),
    title="OpenAI with RAG and Function calling",
    description="Ask a question",
    theme="soft",
    retry_btn=None
).launch()