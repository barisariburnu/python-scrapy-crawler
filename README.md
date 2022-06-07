# Python Scrapy Udemy

It is an application where all course content published on udemy api is scrapped.

### Install 

1. Clone repository
    - `cd /home/ubuntu`
    - `git clone https://github.com/barisariburnu/python_scrapy_udemy.git`

2. Change current directory
    - `cd /home/ubuntu/python_scrapy_udemy`

3. Create virtual environment and install requirements into it
    - `python3 -m venv venv3`
    - `source venv3/bin/activate`
    - `pip install --upgrade pip`
    - `pip install -r requirements.txt`

4. Start scrapy script
    - `python3 scrapy crawl udemy`

### Configuration

1. Install and enable cron
    - `sudo apt install cron`
    - `sudo systemctl enable cron`

2. Edit crontab
    - `crontab -e`

3. Add to bottom line 
    - `30 * * * * /home/ubuntu/python_scrapy_udemy/service.sh`

4. Save and exit.

### Note

At the moment, the `requirements.txt` is not necessary. The project doesn't
use any packages outside of the Python standard library. Eventually, I plan
to show some more advanced features that will use packages from PyPI.
