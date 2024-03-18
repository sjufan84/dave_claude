import streamlit as st
from typing import List
import logging
import markdown
from anthropic import Anthropic, MessageStream
from pydantic import BaseModel, Field
import base64
from PIL import Image
from io import BytesIO
from utils.extraction_utils import (
    extract_docx_file_contents, extract_text_file_contents, extract_pdf_file_contents
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = Anthropic(api_key=st.secrets["my_secrets"]["ANTHROPIC_KEY"])

default_initial_message = """ You are a helpful assistant helping the user answer questions\
    and analyze files. """

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "initial_prompt" not in st.session_state:
    st.session_state.initial_prompt = "You are a helpful assistant helping\
    the user answer questions and analyze files."
if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "filesUploaded" not in st.session_state:
    st.session_state.filesUploaded = False
if "currentFileType" not in st.session_state:
    st.session_state.currentFileType = None
if "current_string" not in st.session_state:
    st.session_state.current_string = None
if "isNewSession" not in st.session_state:
    st.session_state.isNewSession = True

class VisionMessageRequest(BaseModel):
    file_type: str = Field(..., description="The type of file uploaded. Must be one of\
     JPEG, JPG, PNG, GIF, or WebP")
    image_content: str = Field(..., description="The image encoded as a base64 string")
    message_content: str = Field(..., description="The message content to send to the assistant")

def encode_image(image_file: BytesIO) -> str:
    # Resize the image to 512x512
    image = Image.open(image_file)
    image = image.resize((512, 512))
    image_file = BytesIO()
    image.save(image_file, format="PNG")
    image_file.seek(0)

    return base64.b64encode(image_file.read()).decode()

def get_initial_message(initial_prompt: str) -> str:
    return f""" The user has specified that they would like to initiate the chat with
    the following system message {initial_prompt}.  Based on this, adapt your style and approach
    to the ensuing conversation.  Return all of your answers in markdown format in the format
    that makes the most sense to you given the context.  If the user asks for specific formatting,
    please adhere to their request.  Your respones will be converted to HTML so make sure to
    use markdown syntax."""

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
                "text": message_params.message_content
            }
        ],
    }

    return image_message

def create_text_message(file_text: str, message_content: str) -> dict:
    text_message = {
        "role" : "user", "content" : f"I have uploaded some text files {file_text}.\
        Can you help answer my questions about them? {message_content}"
    }

    return text_message

def file_upload_handler(uploaded_files):
    st.session_state_filesUploaded = True
    if uploaded_files is not None:
        total_text = ""
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
                    total_text += extracted_text
                elif file_type == "docx":
                    st.write(f"Extracting text from docx file: {file.name}")
                    extracted_text = extract_docx_file_contents(file_contents)
                    st.write(f"Extracted text from docx: {extracted_text}")
                    total_text += extracted_text
                elif file_type == "txt":
                    st.write(f"Extracting text from txt file: {file.name}")
                    extracted_text = extract_text_file_contents(file_contents)
                    st.write(f"Extracted text from txt: {extracted_text}")
                    total_text += extracted_text
                st.session_state.current_string = total_text
                st.session_state.currentFileType = "text"
            elif file_type in ["webP", "png", "jpg", "jpeg", "gif"]:
                st.write(f"Handling image file of type {file_type}")
                file_contents = file.read()
                file_base64 = encode_image(BytesIO(file_contents))
                st.session_state.current_string = file_base64
                st.session_state.currentFileType = file_type
                st.write("Image file appended to chat messages")

            else:
                st.error(f"File type {file_type} not supported. Please upload a pdf, docx, or txt file.")
    else:
        st.warning("Please upload a file")

def main():
    if len(st.session_state.chat_history) == 0:
        st.markdown("""Meet Claude, the cutting-edge Language Model (LLM)
        that surpasses GPT-4 in capability and knowledge. Engage in deep conversations
        on a wide range of topics, as Claude can track up to 350 pages of text.
        A standout feature is the ability to upload documents (and soon images)
        for Claude to analyze, summarize, explain, or help you understand them better.
        You can upload one document at a time and ask questions before moving on to another.
        Make sure to click 'Upload Files' after selecting a file to process it.\n\nClaude
        will remember all documents uploaded per session, so start a new session
        for unrelated topics. With a memory capacity of over 300 pages,
        feel free to explore the limits of Claude's abilities.  Keep in mind, however,
        that the longer the documents / chat history get, the slower Claude will be, so if you are
        done discussing a lengthier document, it may be best to start a new session.\n\nOne other fun
        thing to play around with is the 'Initial Message' feature.  This is what shapes
        how Claude responds to you.  So, for instance, you may want him to respond as if
        he was your advisor, a friend, a teacher, or even a character from a movie (pirates area always
        fun).  If you want to change the initial message, click the button on the sidebar and
        enter a new message\n\nAs this is a new system, please report
        any bugs encountered. Enjoy your experience with Claude!""")
    if st.session_state.filesUploaded:
        st.sidebar.markdown(":red[You have already uploaded a file to the chat.\
            Please ask a question and then you will be able to upload more files.]")
    elif not st.session_state.filesUploaded:
        uploaded_files = st.sidebar.file_uploader(
            "Upload files", type=["pdf", "docx", "txt"],
            label_visibility="collapsed"
        )
        if uploaded_files:
            upload_files_button = st.sidebar.button(
                ":blue[Upload files]", type="secondary", use_container_width=True, key="upload_files_button"
            )
            if upload_files_button:
                # Check to make sure there aren't multiple image files uploaded
                with st.spinner("Processing files..."):
                    st.write("Processing files...")
                    file_upload_handler([uploaded_files])
                    for file in [uploaded_files]:
                        # Check to make sure that the file is not already in the session state
                        if file.name not in st.session_state.uploaded_files:
                            st.session_state.uploaded_files.append(file.name)
                            st.write(f"Uploaded files: {st.session_state.uploaded_files}")
                    st.session_state.filesUploaded = True
                    uploaded_files = None
                    st.rerun()
    if st.session_state.uploaded_files != []:
        st.sidebar.markdown("**:blue[Uploaded files for this session:]**")
        for file in st.session_state.uploaded_files:
            st.sidebar.write(file)
    st.sidebar.markdown("---")

    st.sidebar.markdown("Current Initial Message:")
    new_message = st.sidebar.text_area(
        "Enter a new initial message",
        placeholder=f"{st.session_state.initial_prompt}",
        height=100, label_visibility="collapsed"
    )
    submit_message_button = st.sidebar.button(
        ":blue[Submit new message]", type="secondary", use_container_width=True
    )
    if submit_message_button:
        st.session_state.initial_prompt = new_message
        st.sidebar.success(f"Initial message updated to {new_message}")
        st.rerun()
    start_new_session_button = st.sidebar.button(
        ":red[Start a new session]", type="secondary", use_container_width=True
    )
    if start_new_session_button:
        st.session_state.chat_history = []
        st.session_state.initial_message = default_initial_message
        st.session_state.filesUploaded = False
        st.session_state.uploaded_files = []
        st.success("New session started. Chat history and initial message reset.")
        st.rerun()

    # Display chat messages from history on app rerun
    for message in st.session_state.chat_history:
        logging.debug(f"Displaying message: {message}")
        if message["role"] == "assistant":
            with st.chat_message(message["role"]):
                try:
                    message = markdown.markdown(message["content"])
                    st.markdown("""<div>""" + message + """</div>""", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error displaying message: {e}")
                    st.markdown(message["content"])

        elif message["role"] == "user":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Hey friend, how can I help you today?"):
        if st.session_state.isNewSession:
            st.session_state.isNewSession = False
        logging.info(f"Received user input: {prompt}")
        # Add user message to chat history
        if st.session_state.filesUploaded and st.session_state.currentFileType != "text":
            st.session_state.chat_history.append(
                create_vision_message(
                    VisionMessageRequest(
                        file_type=st.session_state.currentFileType,
                        image_content=st.session_state.current_string,
                        message_content=prompt
                    )
                )
            )
        elif st.session_state.filesUploaded and st.session_state.currentFileType == "text":
            st.session_state.chat_history.append(
                create_text_message(st.session_state.current_string, prompt)
            )
        else:
            st.session_state.chat_history.append({"role": "user", "content": prompt})

        st.session_state.current_string = None
        st.session_state.currentFileType = None
        st.session_state.filesUploaded = False
        uploaded_files = None

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

            with client.messages.stream(
                messages=st.session_state.chat_history,
                model="claude-3-opus-20240229",
                event_handler=StreamHandler,
                system = get_initial_message(st.session_state.initial_prompt),
                max_tokens=3500
            ) as stream:
                final_message = stream.get_final_message()
                message_placeholder.markdown(final_message.content[0].text)
                st.session_state.chat_history.append(
                    {"role" : "assistant", "content" : final_message.content[0].text}
                )
                logging.debug(f"Chat history: {st.session_state.chat_history}")

            st.rerun()
if __name__ == "__main__":
    if st.session_state.is_logged_in:
        main()
    else:
        password_check()
