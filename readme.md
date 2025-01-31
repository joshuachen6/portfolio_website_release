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

`git clone https://github.com/joshuachen6/portfolio_website_release.git`

### Set up virtual environment

`python3 -m venv .venv`

- Linux\MacOS
`source .venv/bin/activate`
- Windows
`.\.venv\Scripts\activate`

### Install dependencies

`pip install -r requirements.txt`

### Create passwords

Create `auth/secrets/password.yaml`
Add the line `public: {Your public password}`
Add the line `private: {Your private password}`
The file `code.png` in this folder contains your one time password code for authenticator apps

## How to run

### Testing

`python3 main.py`

### Deployment

`pip install uwsgi`
`uwsgi uWSGI.ini`
