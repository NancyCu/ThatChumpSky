import streamlit as st

# 3D style for all buttons
st.markdown(
    """
    <style>
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        padding: 0.5em 1em;
        border: none;
        border-radius: 5px;
        box-shadow: 0 4px #2c662d;
    }
    .stButton > button:active {
        box-shadow: 0 2px #2c662d;
        transform: translateY(2px);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Dark mode state
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# Top control buttons aligned to the right
_, col_dark, col_print = st.columns([8, 1, 1])
with col_dark:
    if st.button("Dark Mode", key="dark_mode_toggle"):
        st.session_state.dark_mode = not st.session_state.dark_mode
with col_print:
    if st.button("Print", key="print_button"):
        st.markdown("<script>window.print()</script>", unsafe_allow_html=True)

# Apply dark mode styling
if st.session_state.dark_mode:
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #222;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

st.title("CFG to Chomsky Normal Form Converter")

st.markdown("""
Enter your context-free grammar (CFG) below. Use the following format:

S -> AB | a
A -> aA | ε
B -> b

Separate productions with new lines. Use 'ε' for the empty string.
""")

grammar_input = st.text_area("Enter CFG:", height=200)

# Controls for language generation
max_length = st.slider("Max length of generated words", 1, 10, 4)
max_words = st.slider("Max number of words", 1, 50, 10)

if st.button("Convert to CNF"):
    from cnf_converter import cfg_to_cnf, parse_cfg
    try:
        cfg = parse_cfg(grammar_input)
        cnf, steps = cfg_to_cnf(cfg)
        tab1, tab2 = st.tabs(["Chomsky Normal Form", "Step-by-step"])
        with tab1:
            st.subheader("Chomsky Normal Form:")
            st.code(cnf)
        with tab2:
            st.subheader("Transformation Steps:")
            for title, g in steps:
                st.markdown(f"**{title}:**")
                st.code(g)
    except Exception as e:
        st.error(f"Error: {e}")

if st.button("Generate Language"):
    from cnf_converter import parse_cfg, generate_words
    try:
        cfg = parse_cfg(grammar_input)
        words = generate_words(cfg, max_length=max_length, max_words=max_words)
        st.subheader("Generated Language:")
        table_data = [{"Word": w, "Symbols": " ".join(list(w))} for w in words]
        if table_data:
            st.table(table_data)
        else:
            st.info("No words generated with the given limits.")
    except Exception as e:
        st.error(f"Error: {e}")
