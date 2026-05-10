# 🚊 Bremen Abfahrten — Cloud Deployment

## Auf Railway deployen (kostenlos, 5 Minuten)

### Was du brauchst
- GitHub-Account (kostenlos)
- Railway-Account (kostenlos, mit GitHub anmelden)

---

### Schritt 1: Dateien auf GitHub hochladen

1. Gehe zu **github.com** → einloggen
2. Oben rechts **„+"** → **„New repository"**
3. Name: `bremen-abfahrten` → **„Create repository"**
4. Klicke auf **„uploading an existing file"**
5. Alle Dateien aus diesem Ordner hochladen:
   - `index.html`
   - `server.py`
   - `railway.json`
   - `nixpacks.toml`
6. Klicke **„Commit changes"**

---

### Schritt 2: Auf Railway deployen

1. Gehe zu **railway.app** → **„Login with GitHub"**
2. Klicke **„New Project"**
3. Wähle **„Deploy from GitHub repo"**
4. Wähle dein `bremen-abfahrten` Repository
5. Railway erkennt alles automatisch und deployed

**Fertig!** Nach ~2 Minuten bekommst du eine URL wie:
```
https://bremen-abfahrten-production.up.railway.app
```

Diese URL funktioniert von **jedem Gerät**, **überall**, **24/7** — kein Mac, kein Server, kein Terminal nötig.

---

### App auf dem Handy installieren

**iPhone (Safari):**
Teilen → „Zum Home-Bildschirm" → Hinzufügen

**Android (Chrome):**
Menü (⋮) → „App installieren"

---

### Kosten

Railway bietet **5 $ Guthaben pro Monat kostenlos**.
Dieser Server verbraucht ~0.50–1.50 $ pro Monat → komplett kostenlos.

---

### Updates deployen

Neue `index.html` oder `server.py` auf GitHub hochladen →
Railway deployed automatisch innerhalb von ~1 Minute.
