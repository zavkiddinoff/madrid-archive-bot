# ⚽ Real Madrid Arxiv Bot

> **@losblancosuzbekistan** loyihasi uchun yaratilgan arxiv bot.  
> Bot @zavqiddinov_co tomonidan tayyorlangan.

---

## 📁 Fayl tuzilmasi

```
real_madrid_bot/
├── main.py           ← Bot kodi
├── requirements.txt  ← Kerakli kutubxonalar
├── render.yaml       ← Render konfiguratsiyasi
├── .gitignore        ← Git ignore
└── README.md         ← Shu fayl
```

---

## 🚀 QADAMMA-QADAM YO'RIQNOMA

---

### 1-QADAM — BotFather orqali bot yaratish

1. Telegramda **@BotFather** ga o'ting
2. `/newbot` yuboring
3. Bot nomini kiriting: `Real Madrid Arxiv`
4. Bot username kiriting: `losblancosuz_bot` (yoki boshqa erkin nom)
5. BotFather sizga **TOKEN** beradi → uni saqlang

#### Bot ta'rifini o'rnatish (What can this bot do?)
BotFather'ga quyidagini yuboring:
```
/setdescription
```
Botingizni tanlang, so'ng quyidagi matnni yuboring:

```
Assalomu aleykum. 👋⚽

Men Real Madrid jamoasining arxiv o'yinlari botiman. 🏟️

🤖 Bot @losblancosuzbekistan loyihasi uchun
✍️ @zavqiddinov_co tomonidan tayyorlangan.

━━━━━━━━━━━━━━━━━━━━
💡 Ha aytgancha, grafik dizaynerlik va bot yaratish xizmati kerak bo'lsa @ilhomjon_zavqiddinov'ga murojaat qiling! 🎨
━━━━━━━━━━━━━━━━━━━━
```

---

### 2-QADAM — O'z Telegram ID ingizni olish

1. Telegramda **@userinfobot** ga o'ting
2. `/start` yuboring
3. U sizga **ID** raqamingizni ko'rsatadi → uni saqlang

---

### 3-QADAM — GitHub repozitoriy yaratish

1. [github.com](https://github.com) ga o'ting va akkaunt oching (agar yo'q bo'lsa)
2. **New repository** tugmasini bosing
3. Nom: `real-madrid-arxiv-bot`
4. **Public** tanlang
5. **Create repository** bosing

#### Fayllarni GitHub ga yuklash:
```
main.py
requirements.txt
render.yaml
.gitignore
```

> **Eslatma:** `videos.json` faylini YUKLAMANG — u `.gitignore` ga qo'shilgan.

---

### 4-QADAM — Render'ga deploy qilish

1. [render.com](https://render.com) ga o'ting, GitHub akkauntingiz bilan kiring
2. **New** → **Web Service** bosing
3. GitHub repozitoriyingizni ulang: `real-madrid-arxiv-bot`
4. Quyidagi sozlamalarni kiriting:

| Sozlama | Qiymat |
|---------|--------|
| **Name** | `real-madrid-arxiv-bot` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python main.py` |
| **Plan** | `Free` |

5. **Environment Variables** bo'limiga o'ting va qo'shing:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | BotFather'dan olgan tokeningiz |
| `ADMIN_ID` | @userinfobot'dan olgan ID raqamingiz |

6. **Create Web Service** bosing
7. Deploy tugashini kuting (3-5 daqiqa)

---

### 5-QADAM — Cron Job ulab 24/7 ishlashini ta'minlash

Render free tier 15 daqiqa ichida so'rov bo'lmasa "uxlaydi". Buning oldini olish uchun:

1. [cron-job.org](https://cron-job.org) ga o'ting va bepul akkaunt oching
2. **CREATE CRONJOB** bosing
3. Quyidagilarni to'ldiring:

| Maydon | Qiymat |
|--------|--------|
| **Title** | `Real Madrid Bot Keep Alive` |
| **URL** | `https://real-madrid-arxiv-bot.onrender.com` (Render URL ingiz) |
| **Schedule** | Every 10 minutes |

4. **CREATE** bosing

> ✅ Endi bot 24/7 uyg'oq turadi!

---

## 🎮 BOT ISHLATISH

### Admin sifatida video yuklash:
1. Botga video yuboring
2. Bot sizdan **ID** so'raydi
3. ID kiriting (masalan: `rm_vs_barca_2006`)
4. Bot videoни saqlab qo'yadi ✅

### Foydalanuvchi sifatida video olish:
1. `/start` yuboring
2. O'yin IDsini kiriting
3. Bot videoни yuboradi 📺

---

## ⚠️ MUHIM ESLATMA

> Render'da bepul rejimda **fayl tizimi qayta ishga tushganda tozalanadi** (deploy bo'lganda `videos.json` o'chadi).
>
> **Yechim:** Videolarni qayta yuklamaslik uchun:
> - Videolarni kam o'zgartiring va deploy'lardan so'ng faqat yangi videolar qo'shing
> - Yoki Render'dan **PostgreSQL** bepul bazasini ulab (render.com → New → PostgreSQL) kodni yangilang

---

## 📞 Murojaat

- Loyiha: **@losblancosuzbekistan**
- Bot yaratuvchi: **@zavqiddinov_co**
- Dizayn & Bot xizmati: **@ilhomjon_zavqiddinov**
