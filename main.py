import base64
import io

import PyPDF2
import anthropic
import fitz
import streamlit as st
from PIL import Image
from streamlit_theme import st_theme

api_key = "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"


def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    return text


def file_to_text(file):
    if file.name.endswith('.pdf'):
        return extract_text_from_pdf(file)
    else:
        return file.read().decode()


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def compress_image(image_bytes, quality=20):
    # Open the image from bytes
    image = Image.open(io.BytesIO(image_bytes))

    # Convert image to RGB if it's not in that mode
    if image.mode != 'RGB':
        image = image.convert('RGB')

    # Compress the image and save it as JPEG
    compressed_image_io = io.BytesIO()
    image.save(compressed_image_io, format='JPEG', quality=quality)

    # Get the compressed image bytes
    compressed_image_bytes = compressed_image_io.getvalue()

    return compressed_image_bytes


# returns a list of dictionaries with the following keys:
# - page: page number
# - index: image index on the page
# - extension: image extension
# - base64: base64 encoded image
def extract_images_from_pdf(uploaded_file):
    # Convert the uploaded file buffer to bytes
    pdf_bytes = uploaded_file.getbuffer().tobytes()

    # Open the PDF file from the bytes object
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

    # List to store image data
    images = []

    # Iterate through each page
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]

        # Get the images on the current page
        image_list = page.get_images()

        # Iterate through the images
        for img_index, img in enumerate(image_list):
            # Get the XREF of the image
            xref = img[0]

            # Extract the image bytes
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]

            # Compress the image bytes
            compressed_image_bytes = compress_image(image_bytes)

            # Get image extension
            image_ext = base_image["ext"]

            # Convert compressed image bytes to base64
            base64_image = base64.b64encode(compressed_image_bytes).decode('utf-8')

            # Store image info
            images.append({
                'page': page_num + 1,
                'index': img_index + 1,
                'extension': image_ext,
                'base64': base64_image
            })

    # Close the PDF file
    pdf_document.close()

    return images


def get_theme_image():
    theme = st_theme()
    if theme["base"] == "dark":
        return "skyincap_logo_white.svg"
    else:
        return "skyincap_logo_colored.svg"


with open(get_theme_image(), "r") as svg_file:
    svg_content = svg_file.read()

with st.sidebar:
    st.markdown(f'<div>{svg_content}</div><br>', unsafe_allow_html=True)
    anthropic_api_key = st.text_input("Anthropic API Key", key="file_qa_api_key", type="password")

st.title("📝 Custom AI Agent")

uploaded_file = st.file_uploader("Upload a document", type=("txt", "md", "pdf"))

question = st.text_input(
    "Ask something about the document",
    placeholder="Can you give me a short summary?",
    disabled=not uploaded_file,
)

if uploaded_file and question and not anthropic_api_key:
    st.info("Please add your Anthropic API key to continue.")

if uploaded_file and question and anthropic_api_key:
    article = file_to_text(uploaded_file)
    images = extract_images_from_pdf(uploaded_file)
    prompt = f"""{anthropic.HUMAN_PROMPT} Here's an article:\n\n
    {article}\n\n\n\n{question}{anthropic.AI_PROMPT}"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }
    ]

    for image in images[:10]:
        messages[0]["content"].append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image["base64"]
                }
            }
        )

    client = anthropic.Client(api_key=anthropic_api_key)
    response = client.messages.create(
        model="claude-3-opus-20240229",  # or "claude-3-sonnet-20240229" or "claude-3-haiku-20240229"
        max_tokens=1000,
        messages=messages
    )
    st.write("### Answer")
    st.write(response.content[0].text)
