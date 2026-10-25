import re
from collections import Counter
from urllib.parse import urlparse

import requests
import streamlit as st
from bs4 import BeautifulSoup

st.set_page_config(
    page_title="Smart Web Content Summarizer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1200px;}
    .hero {
        padding: 1.7rem 1.8rem; border-radius: 18px;
        background: linear-gradient(120deg, #153e75, #2563eb);
        color: white; margin-bottom: 1.2rem;
    }
    .hero h1 {color: white; margin: 0 0 .4rem 0; font-size: 2.1rem;}
    .hero p {color: #e7efff; margin: 0; font-size: 1.05rem;}
    .small-note {color: #64748b; font-size: .9rem;}
    div[data-testid="stMetric"] {
        border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px;
        background: #f8fafc;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>🧠 Smart Web Content Summarizer</h1>
  <p>Turn long articles into clear summaries and key points in seconds.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Settings")
    summary_length = st.slider("Summary length", min_value=3, max_value=10, value=5,
                               help="Choose how many sentences to include in the summary.")
    keypoint_count = st.slider("Number of key points", min_value=3, max_value=12, value=6)
    st.divider()
    st.subheader("📌 Features")
    st.markdown(
        "- Extract article text from a public URL\n"
        "- Summarize pasted text\n"
        "- Identify important key points\n"
        "- Show basic content statistics\n"
        "- Download the results as a text file"
    )
    st.caption("Content is processed for this session and is not saved by this app.")

def clean_text(text):
    text = re.sub(r"\s+", " ", text or "")
    return text.strip()

def fetch_article(url):
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Please enter a complete URL starting with https:// or http://.")
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SmartContentSummarizer/1.0)"
    }
    response = requests.get(url.strip(), headers=headers, timeout=18)
    response.raise_for_status()
    if "text/html" not in response.headers.get("Content-Type", "").lower():
        raise ValueError("This link does not appear to be an HTML webpage.")
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form",
                     "noscript", "svg", "iframe"]):
        tag.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else parsed.netloc
    candidates = []
    for selector in ("article", "main", '[role="main"]'):
        for node in soup.select(selector):
            candidate = clean_text(node.get_text(" ", strip=True))
            if len(candidate) > 250:
                candidates.append(candidate)
    if candidates:
        body = max(candidates, key=len)
    else:
        paragraphs = [clean_text(p.get_text(" ", strip=True))
                      for p in soup.find_all(["p", "h1", "h2", "h3", "li"])]
        body = " ".join(p for p in paragraphs if len(p) > 35)
    body = clean_text(body)
    if len(body) < 120:
        raise ValueError("Could not extract enough readable text. Try pasting the article text instead.")
    return title, body

def split_sentences(text):
    # A lightweight sentence splitter that does not need downloaded language models.
    pieces = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"“‘(])", clean_text(text))
    return [s.strip() for s in pieces if len(s.strip()) >= 35]

def summarize(text, n_summary=5, n_points=6):
    sentences = split_sentences(text)
    if not sentences:
        return text[:1200], [text[:250]], 1

    words = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", text.lower())
    stop_words = set("""
        the and for that with this from have has had are was were will would should could
        into about after before over under between their there they them then than also
        your you our out not but all any can may might its it's who what when where which
        while because been being more most some such only very just each other these those
        a an is it in on at to of as by or if be we he she his her i me my do does did
        so no nor too up down than how why use used using based new one two first second
        system content article page website information important key point
    """.split())
    frequencies = Counter(w for w in words if w not in stop_words)
    if not frequencies:
        frequencies = Counter(words)
    max_freq = max(frequencies.values()) if frequencies else 1
    weights = {w: f / max_freq for w, f in frequencies.items()}

    scored = []
    for idx, sentence in enumerate(sentences):
        tokens = [w for w in re.findall(r"[A-Za-z][A-Za-z'-]{2,}", sentence.lower())
                  if w not in stop_words]
        score = sum(weights.get(w, 0) for w in tokens) / max(len(tokens), 1)
        # Slight preference for sentences that are informative but not extremely long.
        if 8 <= len(tokens) <= 35:
            score *= 1.12
        scored.append((score, idx, sentence))
    ranked = sorted(scored, reverse=True)
    chosen = sorted(ranked[:min(n_summary, len(ranked))], key=lambda item: item[1])
    summary = " ".join(item[2] for item in chosen)

    key_ranked = sorted(ranked, key=lambda item: item[0], reverse=True)
    key_points = []
    for _, _, sentence in key_ranked:
        if sentence not in key_points:
            key_points.append(sentence)
        if len(key_points) >= min(n_points, len(sentences)):
            break
    return summary, key_points, len(sentences)

tab_url, tab_text = st.tabs(["🌐 Summarize a URL", "📝 Paste article text"])

def render_results(title, original_text, source_label):
    summary, points, sentence_count = summarize(
        original_text, n_summary=summary_length, n_points=keypoint_count
    )
    words = re.findall(r"\b[\w'-]+\b", original_text)
    summary_words = re.findall(r"\b[\w'-]+\b", summary)
    st.success("Analysis complete.")
    if title:
        st.subheader(title)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Original words", f"{len(words):,}")
    c2.metric("Sentences found", f"{sentence_count:,}")
    c3.metric("Summary words", f"{len(summary_words):,}")
    reduction = max(0, round((1 - len(summary_words) / max(len(words), 1)) * 100))
    c4.metric("Approx. shorter by", f"{reduction}%")

    st.subheader("📄 Summary")
    st.write(summary)
    st.subheader("🔑 Key Points")
    for i, point in enumerate(points, start=1):
        st.markdown(f"{i}. {point}")
    st.subheader("📚 Extracted Text")
    with st.expander("View the full extracted content"):
        st.write(original_text)
    report = (
        f"SMART WEB CONTENT SUMMARIZER\n"
        f"Title: {title or 'Pasted text'}\n"
        f"Source: {source_label}\n\n"
        f"SUMMARY\n{summary}\n\n"
        f"KEY POINTS\n" + "\n".join(f"{i}. {p}" for i, p in enumerate(points, 1)) +
        f"\n\nORIGINAL TEXT\n{original_text}\n"
    )
    st.download_button(
        "⬇️ Download summary and key points (.txt)",
        data=report.encode("utf-8"),
        file_name="smart_web_content_summary.txt",
        mime="text/plain",
        use_container_width=False,
    )

with tab_url:
    st.markdown("Enter a public article or webpage URL. Some websites block automated access.")
    url = st.text_input("Article URL", placeholder="https://example.com/article")
    run_url = st.button("Summarize webpage", type="primary", use_container_width=True)
    if run_url:
        if not url.strip():
            st.warning("Please enter a URL first.")
        else:
            with st.spinner("Fetching and analysing webpage..."):
                try:
                    page_title, article_text = fetch_article(url)
                    render_results(page_title, article_text, url.strip())
                except requests.RequestException as exc:
                    st.error(f"Could not open this webpage: {exc}. Try pasting the article text in the second tab.")
                except ValueError as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("Something went wrong while reading this page. Please try another URL or paste the text.")

with tab_text:
    st.markdown("Paste text from an article, notes, or a study material.")
    pasted_title = st.text_input("Title (optional)", placeholder="e.g. Artificial Intelligence")
    pasted_text = st.text_area("Article text", height=260, placeholder="Paste your content here...")
    run_text = st.button("Summarize pasted text", type="primary", use_container_width=True)
    if run_text:
        if len(pasted_text.strip()) < 80:
            st.warning("Please paste at least a few sentences (80 characters or more).")
        else:
            render_results(pasted_title.strip() or "Pasted Article", clean_text(pasted_text), "Pasted text")

st.divider()
st.markdown(
    "<p class='small-note'>Mini project demonstration • Python + Streamlit + BeautifulSoup • "
    "The summary is extractive and may need human review for academic or professional use.</p>",
    unsafe_allow_html=True,
)
