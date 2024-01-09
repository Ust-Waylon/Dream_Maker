import openai
import gradio as gr
import time
from prompt import music_system_content

def init_messages(system_content):
    return [
        {"role": "system", "content": system_content}
    ]

def append_assistant_message(messages, assistant_content):
    messages.append({"role": "assistant", "content": assistant_content})

def append_user_message(messages, user_content):
    messages.append({"role": "user", "content": user_content})
    
def get_response(messages):
    openai.api_key = "9caacd23ebca451593bf09eda10b006f"
    openai.api_base = "https://hkust.azure-api.net"
    openai.api_type = "azure"
    openai.api_version = "2023-05-15"
    
    response = openai.ChatCompletion.create(
        # engine="gpt-35-turbo-16k",
        engine="gpt-4-32k",
        messages=messages
    )
    
    return response.choices[0].message.content

if __name__ == "__main__":

    video_prompt = "traditional house, snow mountain, calm, sunny"

    system_content = music_system_content(video_prompt)
    
    # build an interface using gradio
    with gr.Blocks() as demo:
        messages = init_messages(system_content)
        
        gr.Markdown(
        """
        # Dream-maker Demo for music-generation
        Type to chat with our chatbot.
        """)
        
        greet_message = """
        Your video is now generating! Now let's talks about the background music!
        How would you like your music? You can describe the style, mood, instruments, tempo, etc.
        """
        append_assistant_message(messages, greet_message)
        init_response = get_response(messages)
        append_assistant_message(messages, init_response)
        init_response = f"""{greet_message}
        Your video prompt is set to be: {video_prompt}
        {init_response}
        """
        
        chatbot = gr.Chatbot(show_copy_button=True, value=[[None, init_response]])
        msg = gr.Textbox()
        # clear = gr.ClearButton([msg, chatbot])

        def respond(message, chat_history):
            append_user_message(messages, message)
            bot_message = get_response(messages)
            chat_history.append((message, bot_message))
            return "", chat_history

        msg.submit(respond, [msg, chatbot], [msg, chatbot])
        
    demo.launch()
    