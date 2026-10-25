# Smart Web Content Summarizer and Key Point Extractor

A deploy-ready Python mini project built with Streamlit.

## Features
- Accepts a public webpage URL and extracts readable text.
- Also supports text pasted directly into the app.
- Creates an extractive summary using sentence scoring and word frequency.
- Lists key points.
- Displays word/sentence statistics.
- Downloads summary, key points, and original text as a `.txt` file.
- Responsive web interface suitable for laptop and mobile.

## Run locally
1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Install packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the app:
   ```bash
   streamlit run app.py
   ```
5. Streamlit will show a local URL such as `http://localhost:8501`.

## Publish as a live website (free Streamlit Community Cloud)
A public live URL requires deployment to a hosting account. This project is ready for that:

1. Sign in to GitHub and create a **public** repository, e.g. `smart-web-content-summarizer`.
2. Upload `app.py`, `requirements.txt`, and `README.md` from this folder to the repository root.
3. Open `https://share.streamlit.io/` and sign in with GitHub.
4. Choose **Create app**, select your repository and branch, and set the main file path to `app.py`.
5. Click **Deploy**. Once deployment finishes, Streamlit will provide a public URL.
6. Open the provided URL to test it on mobile and desktop.

I cannot create the public URL from this chat without access to your hosting account and its deployment approval. Do not share your GitHub password or verification codes in chat.

## Important notes
- Some websites block automated requests, require login, or load article text with JavaScript. For those pages, copy the article text into the second tab.
- The summarizer is extractive (selects important sentences), not a generative AI model. Review outputs before relying on them.
- This demo does not save user text to a database.
