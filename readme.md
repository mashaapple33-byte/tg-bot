How to install
==============

**[ ! ] REQUIRE python >= 3.10.11 [ ! ]**

With Docker
--------------

1. Copy and rename file `.env.example` to `.env`, after this, fill environments variables with your data
2. Run containers: `docker-compose up -d`

Without Docker
--------------

1. Create virtual environment: `python -m venv .venv`
2. Activate your virtual environment:

- For windows: `.venv\Scripts\activate`
- For linux(debians dist.): `source .venv/bin/activate`

3. Install requirements: `pip install -r requirements.txt`
4. Copy and rename file `.env.example` to `.env`, after this, fill environments variables with your data
5. Run bot: `python main.py`