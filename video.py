import openai
import gradio as gr
import time

def init_messages(system_content):
    return [
        {"role": "system", "content": system_content}
    ]

def append_assistant_message(messages, assistant_content):
    messages.append({"role": "assistant", "content": assistant_content})

def append_user_message(messages, user_content):
    messages.append({"role": "user", "content": user_content})
    
def get_response(messages):
    openai.api_key = "f0bf0799408d4ec3bda899ec85adb877"
    openai.api_base = "https://hkust.azure-api.net"
    openai.api_type = "azure"
    openai.api_version = "2023-05-15"
    
    response = openai.ChatCompletion.create(
        engine="gpt-35-turbo-16k",
        messages=messages
    )
    
    return response.choices[0].message.content

if __name__ == "__main__":
    system_content = """
    Now you are acting as a communicator module with user and a translator to translate a natural language description into a prompt for a text-to-video generation model (like stable-diffusion). 
    I will give you a scene description, and finally you need to output a list of words or phrases that describe the scene or indicate the elements that need to be included in the video.
    Since I might not be able to provide sufficient information at the beginning, you can ask me questions to get more information.
   
    Here are some suggested questions for you to ask, you need to use at least 3 of them:
    You should only ask one question at a time.
    Never ask multiple questions at the same time.
    Do NOT ask more than 1 question at a time!!!!
    - Is there a specific theme or concept you want to explore?
    - Should the video be in color or black and white?
    - What is the overall tone or mood you want to create?
    - Do you want any transitions or cuts between different shots?
    - Are there any specific camera angles or perspectives you prefer?
    - How would you describe the desired color palette for the video?
    - Is there anything else you would like to add or clarify about your vision for the video?
    - Any specific camera angle or focus on the main body you'd prefer?
    - Would you like any particular style for the video, such as slow motion, upbeat, scenic, or any specific mood or music?

    You can also ask me other questions if you think that's neccessary.

    
    If a question is already been asked before, do not ask it again.
    If no more useful information is obtained from user, then generate a general scene description.
    Do NOT ask the same question again and again!!!
    You can ask another question or start to generate the prompt.
    If user do not explicitly answer the question, you can ask the question again or choose to ask another question.
    
    If you think you have enough information, you can start to generate the prompt.
    
    Here are some requirements for your output:
    1. The output should be a comma-separated list of words or phrases. Try not to include full sentences (this is very important!!!).
    2. If the description has no main character, add adjectives in describing the scenes.
    3. If the description has a main character, add adjectives in describing the character. Focus on the motion of main character if any.
    4. Use succinct language. Avoid duplicate elements in the list.
    5. Use all details and information provided in user's answer.
    6. Include at least one element that indicates the main body of the scene. Include at least one element that describes the atmosphere.
    7. The final output length is limited to 50 words at most. 
    8. If the prompt input violates OpenAI content policy, halt the process and ask the user to input positive imagery
    
    When you propose a prompt, please clearly state the prompt in a pair of double quotation marks, like this:
    - Here is my prompt: "a light and cheerly EDM track, with syncopated drums, aery pads, and strong emotions bom: 130'
    
    Here are some good examples of output:
    {
        input: "A cute rabbit is leisurely resting in the forest."
        output: "close up photo of a rabbit, forest, haze, halation, bloom, dramatic atmosphere"
    }
    {
        input: "A scene of a coastline, where the wave flapped the reef and stirred layers of spoondrift."
        output: "photo of coastline, rocks, storm weather, wind, waves, lightning"
    }
    """
    
    messages = init_messages(system_content)
    
    # build an interface using gradio
    with gr.Blocks() as demo:
        gr.Markdown(
        """
        # Dream-maker Demo for Video-generation
        Type to chat with our chatbot.
        """)
        greet_message = """
        Hi, this is Dream-maker.
        Tell me anything, and I will turn your dream into a amazing video.
        """
        append_assistant_message(messages, greet_message)
        
        chatbot = gr.Chatbot(show_copy_button=True, show_share_button=True, value=[[None, greet_message]])
        msg = gr.Textbox(label="Chatbox")
        # clear = gr.ClearButton([msg, chatbot])
        clear = gr.ClearButton([msg, chatbot])
        
        def respond(message, chat_history):
            append_user_message(messages, message)
            bot_message = get_response(messages)
            chat_history.append((message, bot_message))
            return "", chat_history

        msg.submit(respond, [msg, chatbot], [msg, chatbot])
        
    demo.launch()
    