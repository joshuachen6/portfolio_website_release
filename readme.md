# Portfolio Website

This is the source code release of my portfolio website

## Features

- Integrated content management system (CMS)
  - Articles
  - Visibility levels
  - User comments
- Embedded article editor
  - Automatic cloud saving
  - Photo and video support
  - Rich text support
- Security
  - Separate admin and guest user passwords
  - Two factor authentication with one time passwords for admin users
  - Session tokens that expire

## How to install

### Clone repository

```bash
git clone https://github.com/joshuachen6/portfolio_website_release.git
```

### Set up virtual environment

```bash
python3 -m venv .venv
```

- Linux\MacOS

```bash
source .venv/bin/activate
```

- Windows

```bash
.\.venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Create passwords

Edit `auth/secrets/password.yaml`. You can change the private and public passwords here. The private is the administrator password and the public is for view access.
The file `code.png` in this folder contains your one time password code for authenticator apps

## How to run

### Testing

```bash
python3 main.py
```

### Deployment

```bash
pip install uwsgi
uwsgi uWSGI.ini
```
