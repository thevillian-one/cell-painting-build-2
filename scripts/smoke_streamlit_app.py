"""Infrastructure-only fixture. Not the project application or scientific output."""
import streamlit as st
st.title("Stage 0 runtime smoke test")
st.write("NO BIOLOGICAL DATA ANALYZED")
if st.button("Confirm runtime"):
    st.success("BUTTON_OK")
