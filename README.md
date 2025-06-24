# Streamify - Movie Recommendation Web Application

Streamify is a Flask-based web application that provides personalized movie recommendations using deep learning.

---

## 📦 Installation Kit

### Prerequisites

Before installing and running Streamify, ensure the following tools are available on your system:

- **Python 3.7 or above**
- **pip** (Python package installer)
- **Visual Studio Code** (recommended IDE)

### Installation Steps

1. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   ```

2. **Change Script Execution Policy (PowerShell on Windows)**
   ```bash
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
   ```

3. **Activate Virtual Environment**
   ```bash
   .\venv\Scripts\Activate.ps1
   ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the Application**
   ```bash
   python run.py
   ```

6. **Deactivate Virtual Environment (when done)**
   ```bash
   deactivate
   ```

---

## 🗃️ Database Setup

To use **DB Browser for SQLite**:

1. [Download DB Browser](https://sqlitebrowser.org/dl/)
2. Open the `site.db` file located in the `instance` folder of the project.
3. You can view tables, browse data, and execute queries visually.

---

## 👥 User Manual

### A. Introduction

Streamify enhances your movie watching experience with personalized recommendations tailored to your unique preferences using deep learning.

### B. System Requirements

#### Hardware:
- **CPU**: Intel Core i5 or higher
- **RAM**: 8GB or more
- **Storage**: 256GB SSD
- **GPU**: 4GB or higher
- **OS**: 32-bit and above

#### Software:
- **OS**: Windows 10+
- **Python**: 3.7+
- **Web Browser**: Google Chrome or equivalent

### C. Installation Guide

Follow the steps under the **Installation Kit** section to set up the application.

### D. Getting Started

1. Launch the app:
   ```bash
   python run.py
   ```
2. Open your browser and go to: `http://127.0.0.1:5000/`
3. Register a new account.
4. Log in and start exploring.

---

## 🚀 Core Features

### ✅ Account Registration (`/signup`)
- Create a new user account with username and password.

### 🔐 User Login (`/login`)
- Log in with your credentials to access features.

### 🏠 Home Page (`/`)
- Browse top-rated and upcoming movies.

### 🎥 Movie Browsing
- **Top-Rated**: View best-rated movies.
- **Upcoming**: Explore upcoming releases.
- **Rated Movies**: See movies you’ve already rated.

### 🔍 Search
- Use the search bar to find any movie quickly.

### 📄 Movie Details Page
- View release date, genres, trailer, and cast.
- Rate movies (1–5 stars) or update/remove your rating.

### 🌟 Personalized Recommendations (`/recommendations`)
- After rating at least one movie, get 20 tailored movie suggestions using the NCF model.

---

## 🛠 Troubleshooting

- **App not starting**: Ensure the virtual environment is activated and all dependencies are installed.
- **Login issues**: Verify correct credentials or re-register.
- **No recommendations**: Make sure you've rated at least one movie.
- **404 Errors**: Confirm the app is running and you're using the right URLs.
