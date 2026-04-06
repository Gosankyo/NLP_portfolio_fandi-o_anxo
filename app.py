import streamlit as st
import ollama

# 1. This creates the Title and Description in your GUI
st.title("📊 Customer Feedback Analyzer")
st.write("Understand your customer reviews quickly with AI!")
st.markdown("---")

# 2. This creates a text box for the user to type or paste the review
review_text = st.text_area("Paste the customer review here:", height=150)

# 3. This creates a button to start the process
if st.button("Analyze Review"):
    
    # Preprocessing: Check if the text is too short
    if len(review_text) < 15:
        st.warning("Please enter a longer review. The AI needs more text to work!")
    else:
        with st.spinner("The AI is thinking..."):
            try:
                # Step 1: Prompt Engineering for Sentiment 
                prompt1 = f"Analyze the sentiment of this review. Answer ONLY with one word: 'Positive', 'Negative', 'Neutral', or 'Mixed'. If the review has both good and bad points, you MUST choose 'Mixed'. Review: '{review_text}'"
                
                response1 = ollama.chat(model='llama3.2', messages=[
                    {'role': 'user', 'content': prompt1}
                ], options={'temperature': 0}) 
                sentiment = response1['message']['content']

                # Step 2: Prompt Engineering for Key Points
                prompt2 = f"List the top 3 key points mentioned in this review as short bullet points. Review: '{review_text}'"
                
                response2 = ollama.chat(model='llama3.2', messages=[
                    {'role': 'user', 'content': prompt2}
                ], options={'temperature': 0}) 
                key_points = response2['message']['content']

                # Postprocessing: Show the results nicely on the screen
                st.success("Analysis Complete!")
                st.subheader("Results")
                st.write(f"**Sentiment:** {sentiment}")
                st.write("**Key Points:**")
                st.write(key_points)

            except Exception as e:
                st.error("Error communicating with Ollama. Make sure the Ollama app is open in the background!")