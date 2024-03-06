import streamlit as st
import os
from dotenv import load_dotenv
import logging
from anthropic import Anthropic, MessageStream

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_KEY"))

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

initial_message = """ You are a master coder, engineer, and start-up advisor helping the user to debug
    their code and offer encouraging and valuable advice on how to improve their code
    and run their start-up. You are a master of your craft and are always ready to help
    your fellow coders and entrepreneurs. """

def main():
    # Accept user input
    st.write(st.session_state.chat_history)
    if prompt := st.chat_input("Hey friend, let's start writing!"):
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
            with client.messages.stream(
                messages=st.session_state.chat_history,
                model="claude-3-opus-20240229",
                event_handler=StreamHandler,
                system = initial_message,
                max_tokens=1250
            ) as stream:
                final_message = stream.get_final_message()
                message_placeholder.markdown(final_message.content[0].text)
                st.session_state.chat_history.append(
                    {"role" : "assistant", "content" : final_message.content[0].text}
                )
                logging.debug(f"Chat history: {st.session_state.chat_history}")

if __name__ == "__main__":
    main()
