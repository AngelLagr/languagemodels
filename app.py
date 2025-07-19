import streamlit as st
import languagemodels as lm
from languagemodels import (
    extract_text_from_pdf,
    complete,
    do,
    embed,
    chat,
    code,
    extract_answer,
    classify,
    store_doc,
    load_doc,
    get_doc_context,
    get_web,
    get_wiki,
    get_weather,
    get_date,
    count_tokens,
)

st.set_page_config(page_title="Language Models Interface", layout="wide")
st.title("🤖 Language Models Playground")

# === Model Configuration ===
st.sidebar.header("🔧 Configuration")

available_models = [
    "LaMini-Flan-T5-783M",
    "Mistral-7B-Instruct-v0.2",
    "flan-t5-xl",
    "flan-alpaca-gpt4-xl",
    "openchat-3.5-0106"
]

selected_model = st.sidebar.selectbox("🔄 Choose Model", available_models)
if st.session_state.get('current_model') != selected_model:
    with st.spinner("Loading model... This may take a moment for first-time downloads."):
        lm.config['instruct_model'] = selected_model
        st.session_state['current_model'] = selected_model

# === RAM Configuration ===
available_ram = ["0.5gb", "1gb", "2gb", "4gb", "8gb"]
selected_ram = st.sidebar.selectbox("🧠 RAM Limit", available_ram)
lm.config["max_ram"] = selected_ram

# === Task Selection ===
option = st.sidebar.selectbox(
    "📋 Choose Task",
    (
        "💬 Chat",
        "📄 Document Q&A",  # Replaces Web Tools
        "🧠 Text Analysis",
        "📋 Instructions",
        "💻 Code Generation",
        "📊 Embeddings",
        "🔧 Utilities",
    ),
)

# === CHAT ===
if option == "💬 Chat":
    st.header("💬 Chat")
    st.info("💡 **Chat** enables natural conversations with AI models. Choose between simple messaging or advanced options with system prompts and document context for enhanced responses.")

    # Chat mode selection
    chat_mode = st.selectbox("Choose chat mode:", ["Simple Chat", "Advanced Chat (Separate Fields)"])

    if chat_mode == "Simple Chat":
        st.subheader("💬 Simple Chat")

        user_input = st.text_area("Your message", height=100,
                                 placeholder="Ask me anything!")

        if st.button("💬 Send"):
            if user_input:
                with st.spinner("Generating response..."):
                    formatted_prompt = f"User: {user_input.strip()}\n\nAssistant:"
                    response = chat(formatted_prompt)
                st.markdown("**Response:**")
                st.write(response)

    elif chat_mode == "Advanced Chat (Separate Fields)":
        st.subheader("💬 Advanced Chat with Separate Fields")

        system_message = st.text_area("System Instructions (optional)", height=80,
                                     placeholder="You are a helpful assistant that provides clear and concise answers.")

        user_message = st.text_area("Your message", height=100,
                                   placeholder="What can you help me with?")

        if st.button("💬 Send Message"):
            if user_message:
                with st.spinner("Generating response..."):
                    formatted_prompt = ""
                    # Ensure system_message and user_message are not None before calling .strip()
                    if system_message and system_message.strip():
                        formatted_prompt += f"System: {system_message.strip()}\n\n"

                    if user_message and user_message.strip():
                        formatted_prompt += f"User: {user_message.strip()}\n\nAssistant:"
                    
                    response = chat(formatted_prompt)
                st.markdown("**Assistant Response:**")
                st.write(response)

# === DOCUMENT Q&A ===
elif option == "📄 Document Q&A":
    st.header("📄 Document Q&A")
    st.info("💡 Load documents from multiple sources, build your knowledge base, and ask intelligent questions. Includes document loading, knowledge management, and advanced research features.")

    # Document Loading Tabs
    st.subheader("📝 Load Documents & Content")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Manual Input", "📚 Wikipedia", "🌐 Web Pages", "📄 Upload PDF", "📂 Manage Knowledge Base"])

    with tab1:
        st.write("**Paste your own content directly**")
        doc_content = st.text_area("Document content", height=150,
                                 placeholder="Paste research papers, articles, policies, meeting notes, etc.")
        doc_name = st.text_input("Document name", placeholder="e.g., 'Research Paper 2024'")

        if st.button("📥 Load Document", key="manual_load"):
            if doc_content:
                with st.spinner("Loading document..."):
                    store_doc(doc_content, doc_name if doc_name else "Manual Document")
                st.success("✅ Document loaded successfully!")

    with tab2:
        st.write("**Automatically fetch Wikipedia articles**")
        wiki_topics = st.text_input("Topics (comma-separated)",
                                   placeholder="Python programming, Machine Learning, Climate Change")

        col1,col2 = st.columns([2, 1])
        with col1:
            if st.button("📚 Load Wikipedia Articles", key="wiki_load"):
                if wiki_topics:
                    topics = [topic.strip() for topic in wiki_topics.split(",")]
                    with st.spinner("Loading Wikipedia articles..."):
                        loaded_count = 0
                        for topic in topics:
                            wiki_content = get_wiki(topic)
                            if wiki_content != "No matching wiki page found.":
                                store_doc(wiki_content, f"Wikipedia: {topic}")
                                loaded_count += 1
                        st.success(f"✅ Loaded {loaded_count}/{len(topics)} Wikipedia articles!")

    with tab3:
        st.write("**Extract content from web pages**")
        urls = st.text_area("Web URLs (one per line)", height=100,
                           placeholder="https://example.com/article1\nhttps://news.site/article2\nhttps://blog.com/post")

        col1,col2 = st.columns([2, 1])
        with col1:
            if st.button("🌐 Load Web Pages", key="web_load"):
                if urls:
                    url_list = [url.strip() for url in urls.split('\n') if url.strip()]
                    with st.spinner("Loading web pages..."):
                        loaded_count = 0
                        for url in url_list:
                            web_content = get_web(url)
                            # Truncate content preview to the first 300 characters
                            if web_content and web_content.strip():
                                truncated_content = web_content[:300] + "..." if len(web_content) > 300 else web_content
                                store_doc(truncated_content, f"Web: {url}")
                                loaded_count += 1
                        st.success(f"✅ Loaded {loaded_count}/{len(url_list)} web pages!")
        
    with tab4:
        st.write("**Upload and process PDF files**")
        uploaded_pdf = st.file_uploader("Choose a PDF file", type="pdf")
        pdf_name = st.text_input("Document name for the PDF", placeholder="e.g., 'Uploaded PDF Document'")

        if st.button("📥 Process PDF", key="pdf_load"):
            if uploaded_pdf:
                with st.spinner("Processing PDF..."):
                    
                    pages_pdf_text = extract_text_from_pdf(uploaded_pdf)
                    for i, page_text in enumerate(pages_pdf_text):
                        if page_text.strip():
                            store_doc(page_text, f"{pdf_name}_page_{i+1}" if pdf_name else f"Uploaded PDF Page {i+1}")
                        else:
                            st.warning("⚠️ No text could be extracted from the PDF.")
                    st.success("✅ PDF processed and loaded successfully!")

    with tab5:
        st.write("**Manage Knowledge Base**")
        knowledge_files = [doc.name for doc in lm.docs.docs]  # Accessing self.docs directly
        if not knowledge_files:
            st.info("No files in the knowledge base.")
        else:
            for idx, file_name in enumerate(knowledge_files):
                with st.expander(file_name):
                    file_content = next((doc.content for doc in lm.docs.docs if doc.name == file_name), "")
                    # Add a unique key by combining file_name with the index
                    st.text_area("File Preview:", value=file_content[:500], height=150, disabled=True, key=f"file_preview_{idx}")

                    if st.button(f"❌ Delete {file_name}", key=f"delete_{idx}"):
                        lm.docs.docs = [doc for doc in lm.docs.docs if doc.name != file_name]  # Remove the document
                        st.success(f"✅ {file_name} deleted successfully!")


    # Research & Analysis Questions
    st.subheader("❓ Research & Analysis")

    question = st.text_area("Your research question", height=100,
                           placeholder="Examples:\n• What are the main themes in these documents?\n• How do these sources compare on topic X?\n• What evidence supports conclusion Y?\n• Summarize the key findings about Z")

    with st.expander("🔧 Advanced Options"):
        answer_style = st.selectbox("Answer style:",
                                   ["Comprehensive", "Concise", "Bullet Points", "Comparative Analysis"])
        include_sources = st.checkbox("Show source references", value=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🔍 Research & Analyze", key="main_research"):
            if question:
                with st.spinner("Analyzing documents and generating insights..."):
                    context = get_doc_context(question)
                    if context and context.strip():
                        styled_question = question
                        if answer_style == "Concise":
                            styled_question = f"Answer concisely: {question}"
                        elif answer_style == "Bullet Points":
                            styled_question = f"Answer in bullet points: {question}"
                        elif answer_style == "Comparative Analysis":
                            styled_question = f"Provide a comparative analysis for: {question}"
                        answer = extract_answer(styled_question, context)

                        st.markdown("**Research Results:**")
                        st.write(answer)

                        if include_sources:
                            with st.expander("📄 Source Documents & Context"):
                                st.text_area("Relevant sections from your documents:",
                                            value=context, height=200, disabled=True)
                                if "Wikipedia:" in context:
                                    st.info("🔵 Includes Wikipedia content")
                                if "Web:" in context:
                                    st.info("🔵 Includes web page content")
                    else:
                        st.warning("⚠️ No relevant documents found in knowledge base.")
                        st.info("💡 Try loading some documents first using the tabs above!")
        
# === TEXT ANALYSIS ===
elif option == "🧠 Text Analysis":
    st.header("🧠 Text Analysis")
    st.info("💡 **Text Analysis** processes and analyzes text content. It includes classification and text completion.")

    analysis_type = st.selectbox("Choose analysis type:",
                                ["Text Classification", "Text Completion"])  # Question answering removed here

    if analysis_type == "Text Classification":
        st.subheader("📊 Text Classification")
        doc = st.text_area("Text to classify")
        label1 = st.text_input("Label 1 (e.g., 'positive')")
        label2 = st.text_input("Label 2 (e.g., 'negative')")
        if st.button("🔍 Classify"):
            if doc and label1 and label2:
                with st.spinner("Classifying text..."):
                    result = classify(doc, label1, label2)
                st.success(f"Classification: **{result}**")

    elif analysis_type == "Text Completion":
        st.subheader("✍️ Text Completion")
        prompt = st.text_area("Text to complete", height=100)
        if st.button("✨ Complete"):
            if prompt:
                with st.spinner("Completing text..."):
                    completion = complete(prompt)
                st.markdown("**Completion:**")
                st.write(completion)

# === INSTRUCTIONS ===
elif option == "📋 Instructions":
    st.header("📋 Instructions")
    st.info("💡 **Instructions** follow specific commands with precision. Unlike open chat, this executes exact tasks and can limit responses to predefined choices for controlled, predictable outputs.")

    st.subheader("🎯 Task Instructions")

    instruction = st.text_area("Enter your instruction", height=100,
                             placeholder="Examples:\n• Translate to French: Hello world\n• Classify this email: [email content]\n• Pick the best option from: A, B, C")

    use_choices = st.checkbox("🎯 Limit possible answers", help="Restrict the AI to only choose from specific options")

    if use_choices:
        choices = st.text_input("Possible answers (comma-separated)",
                               placeholder="red, blue, green")
        st.caption("The AI will only be able to choose from these options")
    else:
        choices = None

    if st.button("▶️ Execute"):
        if instruction:
            with st.spinner("Processing instruction..."):
                choice_list = [c.strip() for c in choices.split(",")] if choices else None
                result = do(instruction, choice_list)
            st.markdown("**Result:**")
            st.write(result)

            if choice_list:
                st.success(f"✅ Answer was limited to: {', '.join(choice_list)}")

# === CODE GENERATION ===
elif option == "💻 Code Generation":
    st.header("💻 Code Generation")
    st.info("💡 **Code Generation** creates programming code based on your descriptions. The AI specializes in Python but can generate code in various languages when specified.")

    code_prompt = st.text_area("Describe the code you want to generate", height=100,
                              placeholder="# Create a function that calculates fibonacci numbers\ndef fibonacci(n):")

    if st.button("🚀 Generate Code"):
        if code_prompt:
            with st.spinner("Generating code..."):
                generated_code = code(code_prompt)
            st.markdown("**Generated Code:**")
            st.code(generated_code, language='python')

# === EMBEDDINGS ===
elif option == "📊 Embeddings":
    st.header("📊 Text Embeddings")
    st.info("💡 **Embeddings** convert text into numerical vectors that capture semantic meaning. These numbers represent the 'meaning' of text and are used for similarity search, recommendations, and machine learning.")

    embedding_text = st.text_area("Text to embed", height=100)

    if st.button("🔢 Generate Embedding"):
        if embedding_text:
            with st.spinner("Generating embedding..."):
                embedding = embed(embedding_text)
            st.markdown("**Embedding Vector:**")
            st.json(embedding)
            st.info(f"Vector dimensions: {len(embedding)}")

# === UTILITIES ===
elif option == "🔧 Utilities":
    st.header("🔧 Utilities")
    st.info("💡 **Utilities** provide helpful tools for working with text and AI models. Count tokens to understand text length for the AI, get the current date and time, or fetch weather data for any location.")

    utility_tool = st.selectbox("Choose utility:", ["Token Counter", "Current Date", "Weather Info"])

    if utility_tool == "Token Counter":
        st.subheader("🔢 Token Counter")
        text_to_count = st.text_area("Text to analyze", height=100)
        if st.button("🔢 Count Tokens"):
            if text_to_count:
                with st.spinner("Counting tokens..."):
                    token_count = count_tokens(text_to_count)
                st.success(f"Token count: **{token_count}**")

    elif utility_tool == "Current Date":
        st.subheader("📅 Current Date")
        if st.button("📅 Get Current Date"):
            with st.spinner("Getting date..."):
                current_date = get_date()
            st.success(f"Current date: **{current_date}**")

    elif utility_tool == "Weather Info":
        st.subheader("🌤️ Weather Information")
        col1, col2 = st.columns(2)
        with col1:
            lat = st.number_input("Latitude", format="%.6f")
        with col2:
            lon = st.number_input("Longitude", format="%.6f")
        if st.button("🌤️ Get Weather"):
            if lat and lon:
                with st.spinner("Fetching weather data..."):
                    weather = get_weather(lat, lon)
                st.markdown("**Weather:**")
                st.write(weather)
