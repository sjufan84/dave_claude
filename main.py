import streamlit as st
from typing import List
import logging
from anthropic import Anthropic, MessageStream
from pydantic import BaseModel, Field
import base64
from io import BytesIO
from utils.extraction_utils import (
    extract_docx_file_contents, extract_text_file_contents, extract_pdf_file_contents
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = Anthropic(api_key=st.secrets["my_secrets"]["ANTHROPIC_KEY"])

default_initial_message = """ You are a helpful assistant helping the user answer questions\
    and analyze files. """

initial_uploaded_file_message = [
    {
        "role": "user",
        "content": "I am uploading some files that I would like to ask you some questions about.\
            These may be image files, text files, or some combination of both."
    }
]

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "initial_message" not in st.session_state:
    st.session_state.initial_message = "You are a helpful assistant helping\
    the user answer questions and analyze files."
if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False
if "file_chat_messages" not in st.session_state:
    st.session_state.file_chat_messages = []
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []


class VisionMessageRequest(BaseModel):
    file_type: str = Field(..., description="The type of file uploaded. Must be one of\
     JPEG, JPG, PNG, GIF, or WebP")
    image_content: str = Field(..., description="The image encoded as a base64 string")

def encode_image(image_file: BytesIO) -> str:
    return base64.b64encode(image_file.read()).decode()

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


def create_vision_message(message_params: VisionMessageRequest) -> List[dict]:
    """ Create a message from the user input and image. """
    # Check to make sure that the file type is an image
    if message_params.file_type not in ["jpg", "jpeg", "png", "gif", "webP"]:
        raise ValueError("File type must be one of JPEG, JPG, PNG, GIF, or WebP")
    image_message = {
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": f"image/{message_params.file_type}",
                    "data": message_params.image_content
                },
            },
            {
                "type": "text",
                "text": "Can you help me answer\
                some questions about this image?"
            }
        ],
    }

    return image_message

def create_text_message(file_text: str) -> List[dict]:
    text_message = {
        "role" : "user", "content" : f"Can you help me answer questions\
            about this text that I have uploaded? {file_text}"
    }

    return text_message

def file_upload_handler(uploaded_files):
    if uploaded_files is not None:
        for file in uploaded_files:
            # If the file is already in the session state, skip it
            if file.name in st.session_state.uploaded_files:
                st.warning(f"File {file.name} has already been uploaded")
                continue
            file_type = file.name.split(".")[-1]
            if file_type in ["pdf", "docx", "txt"]:
                st.write(f"Handling file of type {file_type}")
                file_contents = file.read()
                if file_type == "pdf":
                    st.write(f"Extracting text from pdf file: {file.name}")
                    extracted_text = extract_pdf_file_contents(file_contents)
                    st.write(f"Extracted text from pdf: {extracted_text}")
                    st.session_state.file_chat_messages.append(create_text_message(extracted_text))
                    st.write(f"PDF text appended to chat messages: {st.session_state.file_chat_messages}")
                elif file_type == "docx":
                    st.write(f"Extracting text from docx file: {file.name}")
                    extracted_text = extract_docx_file_contents(file_contents)
                    st.write(f"Extracted text from docx: {extracted_text}")
                    st.session_state.file_chat_messages.append(create_text_message(extracted_text))
                    st.write(f"Docx text appended to chat messages: {st.session_state.file_chat_messages}")
                elif file_type == "txt":
                    st.write(f"Extracting text from txt file: {file.name}")
                    extracted_text = extract_text_file_contents(file_contents)
                    st.write(f"Extracted text from txt: {extracted_text}")
                    st.session_state.file_chat_messages.append(create_text_message(extracted_text))
                    st.write(f"Txt text appended to chat messages: {st.session_state.file_chat_messages}")
            elif file_type in ["jpg", "png", "jpg", "jpeg"]:
                st.write(f"Handling image file of type {file_type}")
                file_contents = file.read()
                file_base64 = encode_image(BytesIO(file_contents))
                st.session_state.file_chat_messages.append(
                    create_vision_message(
                        VisionMessageRequest(
                            file_type=file_type,
                            message_content="",
                            image_content=file_base64
                        )
                    )
                )
                st.write("Image file appended to chat messages")

            else:
                st.error(f"File type {file_type} not supported. Please upload a pdf, docx, or txt file.")
    else:
        st.warning("Please upload a file")

def main():
    st.sidebar.markdown(":blue[Upload files to chat with Claude about:]")
    uploaded_files = None
    uploaded_files = st.sidebar.file_uploader(
        "Upload files", type=["pdf", "docx", "txt", ".png", ".jpg", ".jpeg"],
        label_visibility="collapsed", accept_multiple_files=True,
    )
    if uploaded_files:
        upload_files_button = st.sidebar.button(
            ":blue[Upload files]", type="secondary", use_container_width=True, key="upload_files_button"
        )
        if upload_files_button:
            with st.spinner("Processing files..."):
                st.write("Processing files...")
                file_upload_handler(uploaded_files)
                for file in uploaded_files:
                    # Check to make sure that the file is not already in the session state
                    if file.name not in st.session_state.uploaded_files:
                        st.session_state.uploaded_files.append(file.name)
                        st.write(f"Uploaded files: {st.session_state.uploaded_files}")
                uploaded_files = None
                st.rerun()
    if st.session_state.uploaded_files != []:
        st.sidebar.markdown("**:blue[Uploaded Files:]**")
        for file in st.session_state.uploaded_files:
            st.sidebar.write(file)
    st.sidebar.markdown("---")

    adjust_initial_message_button = st.sidebar.button(
        ":violet[Adjust initial message]", type="secondary", use_container_width=True
    )
    if adjust_initial_message_button:
        new_message = st.sidebar.text_area(
            "Enter a new initial message",
            placeholder=f"Current message: {st.session_state.initial_message}",
            type="secondary", use_container_width=True
        )
        submit_message_button = st.sidebar.button("Submit new message")
        if submit_message_button:
            st.session_state.initial_message = get_initial_message(new_message)
            st.sidebar.success(f"Initial message updated to {new_message}")

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
        st.write(f"Chat history: {st.session_state.chat_history}")

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
            if len(st.session_state.file_chat_messages) > 0:
                st.session_state.chat_history_messages = initial_uploaded_file_message + st.session_state.file_chat_messages
                messages = st.session_state.chat_history + st.session_state.file_chat_messages
                st.write(f"File chat messags {st.session_state.file_chat_messages}\
                added to chat history")
            else:
                messages = st.session_state.chat_history

            st.stop()

            with client.messages.stream(
                messages=messages,
                model="claude-3-opus-20240229",
                event_handler=StreamHandler,
                system = st.session_state.initial_message,
                max_tokens=3500
            ) as stream:
                st.write(f"Current initial message: {st.session_state.initial_message}")
                final_message = stream.get_final_message()
                message_placeholder.markdown(final_message.content[0].text)
                st.session_state.chat_history.append(
                    {"role" : "assistant", "content" : final_message.content[0].text}
                )
                logging.debug(f"Chat history: {st.session_state.chat_history}")
                # Reset the file chat messages
                st.session_state.file_chat_messages = []
                # Reset the uploaded files
                uploaded_files = None

if __name__ == "__main__":
    if st.session_state.is_logged_in:
        main()
    else:
        password_check()
