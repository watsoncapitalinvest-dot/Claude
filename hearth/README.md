# 🔥 Hearth

**A private, shared home base for your family — money, plans, and everything you do together.**

Hearth is a warm, simple app the two of you can open on your phones and computers to keep the whole household in one place: your money, your bills, your tasks and calendar, shopping lists, meal plans, savings goals, and shared notes.

It's built to be **private and effortless**:

- **Everything stays on your own device.** There's no account to create and no server. Your financial data never leaves your phone or laptop unless *you* choose to export it.
- **Works offline** and installs to your home screen like a real app.
- **Free.** Nothing to host, nothing to pay for.

---

## What's inside

| Area | What it does |
|------|--------------|
| 🏠 **Home** | A daily overview — net worth, spending, upcoming bills, today's plans, tasks, and shopping at a glance. |
| 💰 **Money** | All your accounts and net worth · a spending log · monthly budgets by category · bills & subscriptions with due dates. |
| 🗓️ **Plan** | Shared to-dos (assign them to either of you) and one shared family calendar. |
| 🧺 **Household** | Shopping lists you both can edit · a weekly meal planner · a home inventory for supplies. |
| ✨ **Together** | Shared savings goals (vacation, a new couch, an emergency fund) and a notes space for anything. |

---

## Getting started

### Try it right now
1. Serve the folder with any static web server, for example:
   ```bash
   cd hearth
   python3 -m http.server 8000
   ```
2. Open **http://localhost:8000** in your browser.
3. On first run you'll set your home name, both of your names, and your currency. You can also tap **"Explore with sample data"** to see it filled in first.

### Put it on your phones (installs like an app)
Host the `hearth/` folder anywhere that serves static files over **https** — for example **GitHub Pages**, Netlify, or Vercel (all have free tiers). Then:

- **iPhone (Safari):** open the site → Share → *Add to Home Screen*.
- **Android (Chrome):** open the site → menu → *Install app* / *Add to Home Screen*.

It will open full-screen with its own icon, and work even without a connection.

> **Why https?** Installing as an app and working offline requires a secure origin. `localhost` also counts, which is why the local test above works.

---

## Sharing data between the two of you

Because everything is stored privately on each device, the two of you each have your own copy. To share:

1. Open **Settings → Backup & share → Export backup**. This saves a small `hearth-backup-….json` file.
2. Send it to your partner (AirDrop, text, email, shared drive — whatever's easy).
3. On their device, open **Settings → Import backup** and choose **Merge** (combine with theirs) or **Replace** (use yours).

Export a backup now and then anyway — it's your safety net.

> Want the two of you to see each other's edits **live**, automatically? That's the natural next step (a small optional sync service). The app is built so this can be added later without changing how it works today.

---

## Privacy & security

- **Local-first:** all data lives in your browser's storage on your device. No analytics, no tracking, no cloud.
- **App lock:** turn on a 4-digit PIN in **Settings → Privacy & security** to add a lock screen.
- **Your keys stay yours:** the only way data leaves a device is a backup file you deliberately export.

---

## Built to grow

Hearth is a plain, dependency-free web app (HTML, CSS, and vanilla JavaScript modules) — no build step, no frameworks. That keeps it fast, portable, and easy to wrap into a native iOS/Android app later (e.g. with Capacitor) if you ever want it in the app stores.

```
hearth/
├── index.html              # app shell
├── manifest.webmanifest    # installable-app metadata
├── sw.js                   # service worker (offline support)
├── css/styles.css          # design system
├── icons/                  # app icons
└── js/
    ├── app.js              # bootstrap, shell, lock screen
    ├── store.js            # data + storage (the single source of truth)
    ├── router.js           # navigation
    ├── nav.js              # menu config
    ├── utils.js, ui.js     # helpers, modals, forms
    └── views/              # one file per area (money, plan, household, goals…)
```

Made with care, to make everyday life a little calmer. 🔥
