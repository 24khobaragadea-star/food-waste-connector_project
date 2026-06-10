# 🥗 Food Waste Connector

A web platform that connects surplus food donors with NGOs to reduce food waste and feed people in need.

---

## 🚀 Quick Setup

### 1. Install Python dependencies

```bash
cd food-waste-connector
pip install -r requirements.txt
```

### 2. Run the application

```bash
python app.py
```

### 3. Open in browser

```
http://localhost:5000
```

---

## 👤 Default Admin Login

| Email | Password |
|-------|----------|
| admin@foodconnector.org | admin123 |

---

## 🏗️ Project Structure

```
food-waste-connector/
├── app.py                    # Main Flask application (routes, models, logic)
├── requirements.txt          # Python dependencies
├── instance/
│   └── foodwaste.db          # SQLite database (auto-created)
├── static/
│   ├── css/
│   │   └── style.css         # Complete design system
│   └── js/
│       └── main.js           # Timers, interactions
└── templates/
    ├── base.html             # Navigation, footer, flash messages
    ├── index.html            # Homepage with hero, stats, food listings
    ├── register.html         # Registration with role selector
    ├── login.html            # Login page
    ├── donor_dashboard.html  # Donor dashboard + request management
    ├── add_food.html         # Add food listing form
    ├── ngo_dashboard.html    # NGO dashboard + food browsing
    └── admin_dashboard.html  # Admin panel with tabs
```

---

## 👥 User Roles

### Donor
- Register and list surplus food with full details
- See incoming NGO requests (pending/accepted/rejected)
- Accept or reject requests
- Mark donations as completed
- View full donation history

### NGO
- Register (requires admin verification before requesting food)
- Browse all available donations
- Request food with optional message to donor
- Track request status (pending → accepted → completed)

### Admin
- Login: admin@foodconnector.org / admin123
- Verify pending NGO accounts
- Suspend or activate any user
- Monitor all donations and requests via tabbed dashboard
- View platform-wide statistics

---

## ✨ Features

| Feature | Status |
|---------|--------|
| Donor registration & login | ✅ |
| NGO registration & login | ✅ |
| Admin panel | ✅ |
| Add food listing with expiry | ✅ |
| NGO verification by admin | ✅ |
| Food request system | ✅ |
| Accept/reject requests | ✅ |
| Auto-expire old food | ✅ |
| Expiry countdown timer | ✅ |
| Donation history | ✅ |
| Dashboard analytics | ✅ |
| Meal estimation (JS) | ✅ |
| Prevent duplicate requests | ✅ |
| Mobile-responsive UI | ✅ |

---

## 🔧 Extending the Project

### Add email notifications
Install `flask-mail` and configure SMTP in `app.py`. Send emails on request acceptance.

### Add location search
Integrate Google Maps API. Store lat/lng in the Donation model and use Haversine formula for nearby search.

### Add Android app
Build a React Native or Flutter app that consumes the `/api/donations` JSON endpoint.

### Deploy to production
- Use PostgreSQL instead of SQLite
- Deploy on Heroku, Railway, or a VPS with Gunicorn + Nginx
- Set `DEBUG=False` and use environment variables for secrets

---

## 🌱 Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3 + Flask |
| Database | SQLite (via SQLAlchemy ORM) |
| Frontend | HTML5 + CSS3 + Vanilla JS |
| Fonts | Sora + DM Sans (Google Fonts) |
| Auth | Werkzeug password hashing + Flask sessions |

---

*Built for social impact — reducing food waste, feeding lives.*
