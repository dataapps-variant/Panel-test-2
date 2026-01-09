# Variant Analytics Dashboard - Panel Version

## 📁 File Structure

Upload these files to your GitHub repo **at the root level**:

```
your-repo/                  (ROOT)
├── Dockerfile              ← Required
├── requirements.txt        ← Required
├── cloudbuild.yaml         ← Required
└── app/                    ← Folder
    ├── __init__.py
    ├── app.py              ← Main app
    ├── config.py           ← Configuration
    ├── bigquery_client.py  ← Data layer
    ├── charts.py           ← Chart functions
    ├── colors.py           ← Color utilities
    ├── theme.py            ← Theme settings
    └── assets/
        └── style.css       ← Custom CSS
```

## 🚀 Deploy to Cloud Run

1. Push all files to your GitHub repo
2. Cloud Build will automatically build and deploy
3. Access at: `https://your-app-url.run.app/app`

## ⚠️ Important

- The app is served at `/app` path (not `/`)
- Make sure `GCS_CACHE_BUCKET` environment variable is set in Cloud Run
- Service account needs BigQuery and GCS permissions

## 🔧 Local Testing

```bash
pip install -r requirements.txt
panel serve app/app.py --port 8080 --allow-websocket-origin="*"
```

Open: http://localhost:8080/app
