# Déploiement

## 1. Backend Render

Créer un nouveau service Web Render depuis ce dépôt.

- Runtime : Python
- Root directory : `backend`
- Build command : `pip install -r requirements.txt`
- Start command : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path : `/health`

Variables d'environnement Render :

```env
DB_HOST=...
DB_PORT=3306
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
FRONTEND_ORIGINS=https://votre-site.netlify.app
AUTH_SECRET_KEY=une-longue-valeur-secrete
AUTH_SESSION_SECONDS=28800
AUTH_COOKIE_SECURE=true
AUTH_COOKIE_SAMESITE=none
```

Après déploiement, vérifier :

```text
https://votre-api.onrender.com/health
```

## 2. Frontend Netlify

Créer un nouveau site Netlify depuis ce dépôt.

- Build command : `npm run build`
- Publish directory : `dist`
- Node version : `22`

Variable d'environnement Netlify :

```env
VITE_API_BASE_URL=https://votre-api.onrender.com
```

Après avoir ajouté ou modifié `VITE_API_BASE_URL`, relancer un déploiement Netlify.

## 3. Points importants

- `FRONTEND_ORIGINS` doit contenir l'URL exacte Netlify utilisée par les utilisateurs.
- Si un domaine personnalisé est ajouté, ajouter aussi ce domaine dans `FRONTEND_ORIGINS`.
- Les cookies d'authentification en production utilisent `Secure=true` et `SameSite=none`, nécessaires lorsque Netlify et Render sont sur deux domaines différents.
