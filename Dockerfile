FROM python:latest

WORKDIR /wxpy
COPY . .
RUN python3 setup.py install
RUN pip install Flask==2.0.2 python-dotenv requests pycryptodome requests_toolbelt -i https://pypi.douban.com/simple/

ENTRYPOINT ["python3", "main.py"]