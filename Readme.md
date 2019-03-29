# Installation guild

- Pre-requirements: python3, mysql, pip3 must be installed in your computer.

- Clone this repository by 
    ```
    git clone https://github.com/quanghuy219/soundchat_server.git
    ```

- Go to project folder by `cd /path/to/project/folder`

- Set up database by importing `soundchat.sql` file, or create fresh database named 'soundchat_development' and run `python3 database.py`

- Set up [Virtualenv](https://docs.python.org/3/library/venv.html)
    ```
    python3 -m venv venv
    ```
- Activate virtual environment: 
    ```
    source venv/bin/activate
    ```
- Install all dependencies by 
    ```
    pip3 install -r requirements.txt
    ```
- Start server on local machine by:
    ```
    $ ./start_server.sh
    ```
- Run test:
    ```
    $ ./run_tests.sh
    ```
