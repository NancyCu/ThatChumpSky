import streamlit as st

st.title("CFG to Chomsky Normal Form Converter")

st.markdown("""
Enter your context-free grammar (CFG) below. Use the following format:

S -> AB | a
A -> aA | ε
B -> b

Separate productions with new lines. Use 'ε' for the empty string.
""")

grammar_input = st.text_area("Enter CFG:", height=200)

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
