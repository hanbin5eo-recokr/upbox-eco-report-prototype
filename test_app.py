import streamlit as st
import time

st.title("Hello, World! This is a test.")
st.write("If you can see this text, the basic environment is working correctly.")

# 버튼을 만들어 상호작용이 되는지도 확인
if st.button("Click me"):
    st.success("Button clicked successfully!")

# 동적인 요소가 제대로 작동하는지 확인
st.write("Counting up:")
placeholder = st.empty()
for i in range(10):
    placeholder.text(f"Counter: {i}")
    time.sleep(0.5)
placeholder.text("Done!")
