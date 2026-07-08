# BS ECE 4-4 Wrap

Directory of names + anonymous/signed message wall. Flask + SQLite, no external services needed.

## Run locally

```
pip install -r requirements.txt
ADMIN_PASSWORD=yourpassword SECRET_KEY=anything python3 app.py
```

Visit http://localhost:5000. Admin panel is at `/admin` (log in with `ADMIN_PASSWORD`).

## Deploy to Railway

1. Push this folder to a GitHub repo (or use `railway up` from the CLI directly — no GitHub needed).
2. On [railway.app](https://railway.app), **New Project → Deploy from GitHub repo** (or run `railway init` then `railway up` in this folder).
3. Railway auto-detects Python and uses the `Procfile` (`gunicorn app:app`) to start it. No extra build config needed.
4. **Add a Volume** (Project → your service → Settings → Volumes → New Volume). Mount it at `/data`. This is required — without it, the SQLite database gets wiped every time you redeploy, since Railway's filesystem is otherwise ephemeral.
5. Set environment variables (Service → Variables):
   - `ADMIN_PASSWORD` — your admin login password
   - `SECRET_KEY` — any random string (used to sign login sessions)
   - `DB_PATH` — `/data/app.db` (matches the volume mount path from step 4)
6. Deploy. Railway gives you a public `*.up.railway.app` URL — you can add a custom domain later under Settings → Networking.

## Using it

- Go to `/admin`, log in, add names one at a time.
- Share the homepage link. Each name links to `/p/<their-slug>`, where anyone can leave a message — anonymous is checked by default, they can uncheck it and type their name if they want to be known.
- Messages post instantly, no approval step. If something needs to come down, delete it from `/admin` (each message and each person has a delete button).

## Notes

- Slugs are auto-generated from names (`Juan Dela Cruz` → `juan-dela-cruz`). If two people share a name, the second gets `-2` appended.
- There's no per-person edit — to rename someone, remove and re-add them (this also clears their messages, so do it before they get any).
