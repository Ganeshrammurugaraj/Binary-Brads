# Binary Brads — Web Deployment Edition

## Deploy to Streamlit Community Cloud
1. Create a GitHub repository (for example `Binary-Brads`).
2. Upload **the contents of this folder** to the repository root (`app.py`, `requirements.txt`, `.streamlit/config.toml`, etc.). Do not upload `.env` or API keys.
3. Go to https://share.streamlit.io/ and select **Create app** > **Deploy a public app from GitHub**.
4. Select your repository, branch `main`, and entrypoint `app.py`.
5. Open **Advanced settings** > **Secrets**, and enter:

```toml
GROQ_API_KEY = "YOUR_GROQ_API_KEY"
GROQ_MODEL = "llama-3.3-70b-versatile"
```

6. Deploy and wait for the public URL. Select **Groq** in the sidebar.

## Notes
- Get a Groq API key from https://console.groq.com/keys; usage limits and model availability vary.
- Cloud deployment uses Groq. Local Ollama cannot run on Streamlit Community Cloud without a separately accessible Ollama server.
- All 14 modes, document text Q&A, utilities and export are in `app.py`. Document Q&A uses keyword retrieval, not embeddings.
- The cloud provider receives prompts and any document excerpts included in prompts. Do not upload confidential information.
- Streamlit Community Cloud may sleep inactive apps; free-tier availability and policies may change.
- If the model is unavailable, update `GROQ_MODEL` in Secrets to an active model listed in your Groq account.
