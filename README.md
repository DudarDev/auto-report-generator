# 🚀 AUTO-REPORT-GENERATOR

🎯 Генерує PDF-звіти з Google Таблиць, архівує в ZIP і надсилає клієнтам на email — автоматично або через веб-інтерфейс.

![streamlit-screenshot](https://your-screenshot-link.com) <!-- якщо є -->

---

## 🔍 Огляд

Цей проєкт автоматизує генерацію звітів:
- ✅ Зчитує дані з Google Sheets
- ✅ Формує персоналізовані PDF через HTML шаблони
- ✅ Архівує звіти у ZIP
- ✅ Надсилає email через Gmail SMTP
- ✅ Має Streamlit-інтерфейс для ручного запуску

---

## 🧰 Стек технологій

- 🐍 Python 3.10+
- 📄 Streamlit
- 📬 SMTP (email)
- 🧾 WeasyPrint + Jinja2 (PDF генерація)
- 🔗 Google Sheets API
- 🛠️ Docker (optional), GitHub Actions (soon)

---

## 📸 Демо

![demo-gif](https://your-demo-link.com)

---

## 🧪 Встановлення

```bash
git clone https://github.com/твій_нік/auto-report-generator.git
cd auto-report-generator
pip install -r requirements.txt
streamlit run app.py
