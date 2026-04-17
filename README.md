# Inventory SaaS System

## 🚀 Features
- Product Management
- Category System
- Stock IN / OUT (Race-safe)
- Dashboard Analytics
- 7 Days Chart API
- JWT Authentication

## 🛠 Tech Stack
- Django
- Django REST Framework
- SQLite (dev)

## 📦 API Endpoints

- /api/products/
- /api/categories/
- /api/stock/
- /api/dashboard/
- /api/dashboard/chart/

## ⚙️ Setup

```bash
git clone https://github.com/engrrasel/inventory-saas.git
cd inventory-saas
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver