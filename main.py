import streamlit as st
import os
from dotenv import load_dotenv
import logging
from anthropic import Anthropic, MessageStream

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

client = Anthropic(api_key=st.secrets["my_secrets"]["ANTHROPIC_KEY"])

default_initial_message = """ You are a master coder, engineer, and start-up advisor helping the user to debug
    their code and offer encouraging and valuable advice on how to improve their code
    and run their start-up. You are a master of your craft and are always ready to help
    your fellow coders and entrepreneurs. """


# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "initial_message" not in st.session_state:
    st.session_state.initial_message = default_initial_message
if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False

def get_initial_message(initial_prompt: str) -> str:
    return f""" The user has specified that they would like to initiate the chat with
    the following system message {initial_prompt}.  Based on this, adapt your style and approach
    to the ensuing conversation. """

def password_check():
    password = st.text_input("Enter your password", type="password")
    correct_password = st.secrets["my_secrets"]["CURRENT_PASSWORD"]
    if password == correct_password:
        st.session_state.is_logged_in = True
        st.success("You are now logged in")
        st.rerun()
    else:
        st.error("The password you entered is incorrect")

def main():
    # Accept user input
    if st.session_state.chat_history == []:
        st.markdown("""**:rainbow[@Erik and Babette]** -- Let me introduce you to Claude.\
        He is the latest\
        and greatest of the LLMs, beating GPT-4 on several benchmarks.\
        He has a context window of 200,000 tokens,\
        or about 350 pages of text with virtually perfect recall.\
        So basically that means you could ask questions about\
        an entire (relatively long) book and he would be able to answer them.\
        Feel free to play around with this.\n\nYou will notice on the sidebar where
        there is a text area to enter an initial prompt.\
        This allows you to set up Claude to take on a persona, etc.  Currently it defaults to\
        helping me with coding, but feel free to play around with it\
        to get different results.\n\nI am working\
        on adding in file uploads and image chat, but for now you can\
        go wild with pushing the limits of his knowledge.  Countdown\
        is on to GPT-5...""")
    initial_prompt = st.sidebar.text_area(
        "Input an initial prompt for Claude to guide the conversation",
        placeholder=f"Current prompt: {default_initial_message}",
        height=350
    )
    change_message_button = st.sidebar.button("Change initial message")
    if change_message_button:
        st.session_state.initial_message = get_initial_message(initial_prompt)
        st.sucess(f"Initial message updated to {initial_prompt}")

    # Display chat messages from history on app rerun
    for message in st.session_state.chat_history:
        logging.debug(f"Displaying message: {message}")
        if message["role"] == "assistant":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        elif message["role"] == "user":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Hey friend, how can I help you today?"):
        logging.info(f"Received user input: {prompt}")
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        logger.info(f"Chat history: {st.session_state.chat_history}")

        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            # Create a stream handler
            class StreamHandler(MessageStream):
                def on_stream_event(self, event):
                    if event.type == "content_block_delta":
                        nonlocal full_response
                        full_response += event.delta.text
                        message_placeholder.markdown(full_response + "▌")

            # Start the streaming conversation
            # Filter the chat history to be the last 8 messages
            # as long as the first message has role user

            with client.messages.stream(
                messages=st.session_state.chat_history,
                model="claude-3-opus-20240229",
                event_handler=StreamHandler,
                system = st.session_state.initial_message,
                max_tokens=4000
            ) as stream:
                logger.info(f"Current initial message: {st.session_state.initial_message}")
                final_message = stream.get_final_message()
                message_placeholder.markdown(final_message.content[0].text)
                st.session_state.chat_history.append(
                    {"role" : "assistant", "content" : final_message.content[0].text}
                )
                logging.debug(f"Chat history: {st.session_state.chat_history}")

if __name__ == "__main__":
    if st.session_state.is_logged_in:
        main()
    else:
        password_check()
