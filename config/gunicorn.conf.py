import multiprocessing
bind = '127.0.0.1:8000'
user = "novator"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'gthread'
timeout = 30
threads = 2
max_requests = 1000
max_requests_jitter = 50
keepalive = 2
capture_output = True

