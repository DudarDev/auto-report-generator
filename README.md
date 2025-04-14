# 🧾 AUTO-REPORT-GENERATOR

Генерує PDF-звіти з Google Таблиць, архівує в ZIP і надсилає клієнтам на email — автоматично або через веб-інтерфейс.

![streamlit-screenshot](https://your-screenshot-link.com) <!-- додай скрін -->

---

## 🔍 Огляд

Цей проєкт автоматизує генерацію звітів:

✅ Зчитує дані з Google Sheets  
✅ Формує PDF через HTML-шаблони  
✅ Архівує у ZIP  
✅ Надсилає email через Gmail SMTP  
✅ Має Streamlit-інтерфейс для ручного запуску  

---

## 🧰 Стек технологій

- 🐍 Python 3.12+
- 📊 Streamlit
- ✉️ SMTP (`smtplib`)
- 🧾 WeasyPrint + `jinja2`
- 📑 Google Sheets API
- 🐳 Docker + Google Cloud Run
- 🛠 GitHub Actions (в майбутньому)

---

## 🚀 Деплой на Google Cloud Run

1. Встанови Google Cloud SDK
2. Увійди в акаунт: `gcloud auth login`
3. Встанови проект: `gcloud config set project autoreportbot`

Потім:

```bash
make build      # збірка Docker-образу
make deploy     # деплой у Cloud Run
