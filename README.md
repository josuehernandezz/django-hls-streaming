# Django-HLS-Streaming

**Django-HLS-Streaming** is a Django-based web application that allows users to upload video files and stream them directly in the browser using **HLS (HTTP Live Streaming)**. It handles file upload, background video processing, and segment generation, delivering a smooth, adaptive streaming experience.

---

## 🎯 Project Overview

This project showcases my ability to design and build a **full-stack video streaming platform** using Django, Celery, Redis, and FFmpeg. It mimics the core functionality of platforms like Plex or YouTube at a minimal scale.

Features:
- ✅ Upload videos via the browser
- ✅ Automatically process videos into `.m3u8` HLS format using FFmpeg
- ✅ Segment `.ts` chunks for adaptive browser playback
- ✅ Serve videos securely using Django views and static routing
- ✅ Background task queue powered by Celery and Redis
- ✅ Clean TailwindCSS UI with Flowbite components

This application is designed to be performant, secure, and easily extendable — for example, to add user auth, access controls, or monetization later.

---

## 🚀 Live Demo
> 🔗 `https://django-hls.josueh.dev`*

---

## ⚙️ Tech Stack

| Layer        | Tech                     |
|--------------|--------------------------|
| Backend      | Django, Python           |
| Async Tasks  | Celery, Redis            |
| Video Engine | FFmpeg                   |
| Frontend     | TailwindCSS, Flowbite    |
| Streaming    | HLS (.m3u8 + .hls chunks) |
| Dev Tools    | Docker, docker-compose .env  |

---

## 📁 Repository Structure

- `django/` – Django project
- `media/` – Uploaded + processed video assets
- `node/` – TailwindCSS + Flowbite frontend setup
- `.env` – Environment config for dev
- `requirements.txt` – Python dependencies
- `README.md` – You're here!

---

## 🛠️ Setup Instructions

> Full local development setup — suitable for running in your own environment

### 1. Clone the repository

```bash
git clone git@github.com:josuehernandezz/django-hls-streaming.git
cd Django-HLS-Streaming-streaming
