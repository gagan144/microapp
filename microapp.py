"""
Micro Python Application
"""

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.routing import APIRoute
import sys
import time
import json
import os
import socket
import platform
from datetime import datetime
import psutil
import re
import uuid
import requests
import logging
from pydantic import BaseModel
from typing import Optional
from typing_extensions import Literal
from cpu_load_generator import load_all_cores


# Set Logger
logger = logging.getLogger('uvicorn')
loggerError = logging.getLogger('uvicorn.error')
if len(logger.handlers) == 0:
    print("Configuring debug logger...")
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    loggerError = logger
    logging.basicConfig(format='%(asctime)s|%(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    print("Done!")


# Get Environment variables
PORT = int(os.getenv('APP_PORT', '7000'))
APP_SECRET_TOKEN = str(os.getenv('APP_SECRET_TOKEN', 'secret'))


# Globals
with open("version.json", "r") as f:
    VERSION = json.loads(f.read())["version"]
APP_ID = "microapp"
WORKER_ID = str(uuid.uuid4())[:8]
STARTED_ON = datetime.utcnow()
FORMAT_UTC_DATETIME = "%Y-%m-%dT%H:%M:%SZ"

PATH_SAMPLE_FILE = "data/sample_data.txt"
SAMPLE_FILE_SIZE_MB = 1


# ----- Helpers -----
def get_ip_address():
    try:
        return socket.gethostbyname(socket.gethostname())
    except:
        return None

def get_processor_freq_hz():
    try:
        return psutil.cpu_freq().current / 1000
    except:
        return None

def check_internet(url: str='http://www.google.com/', timeout_sec: int=5) -> bool:
    try:
        _ = requests.head(url, timeout=timeout_sec)
        return True
    except requests.ConnectionError:
        return False
# ----- /Helpers -----


# ----- Create Server -----
logger.info(f"Worker={WORKER_ID} - Initializing service...")
app = FastAPI(
    title = "Micro Python Application",
    description = "Micro python application for testing.",
    version = VERSION,
)


# ----- Routes -----
@app.get("/")
def index():
    list_urls = []
    list_other_urls = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            list_urls.append({
                "name": route.name,
                "path": route.path,
                "methods": list(route.methods)
            })
        else:
            list_other_urls.append({
                "name": route.name,
                "path": route.path,
                "methods": list(route.methods)
            })

    system_users = psutil.users()

    return PlainTextResponse(
        json.dumps({
            "pid": os.getpid(),
            "worker_id": WORKER_ID,
            "id": APP_ID,
            "name": app.title,
            "description": app.description,
            "version": app.version,
            "language": "Python",
            "started_at": STARTED_ON.strftime(FORMAT_UTC_DATETIME),
            "status": "ok",
            "system_info": {
                "host_name": socket.gethostname(),
                "host_ip": get_ip_address(),
                "arch": platform.machine(),
                "processor": platform.processor(),
                "n_processors": psutil.cpu_count(),
                "processor_freq_ghz": get_processor_freq_hz(),
                "memory_mb": round(psutil.virtual_memory().total / (1024.0 **2)),
                "mac_address": ':'.join(re.findall('..', '%012x' % uuid.getnode())),
                "os": platform.system(),
                "os_release": platform.release(),
                "os_version": platform.version(),
                "user": system_users[0].name if len(system_users) else None
            },
            "urls": list_urls,
            "urls_others": list_other_urls,
            "author": "Gagandeep Singh (https://github.com/gagan144)"
        }, indent=4),
        media_type = 'application/json'
    )


@app.get("/health")
def health():
    mem_info = psutil.virtual_memory()

    return JSONResponse({
        "status": "ok",
        "worker_id": WORKER_ID,
        "datetime": datetime.utcnow().strftime(FORMAT_UTC_DATETIME),
        "memory": {
            "total_mb": round(mem_info.total / (1024 ** 2)),
            "used_mb": round(mem_info.used / (1024 ** 2)),
            "available_mb": round(mem_info.available / (1024 ** 2)),
            "usage_perc": mem_info.percent
        },
        "cpu": {
            "usage_perc": psutil.cpu_percent(interval=0.2),

            # load over the last 1, 5 and 15 minutes
            "average_load_perc": [(x / psutil.cpu_count() * 100) for x in psutil.getloadavg()]
        },
        "has_internet_connection": check_internet()
    })


class LoadtestPostData(BaseModel):
    secret_token: str
    handle_id: str
    metadata: Optional[dict] = None
    duration_s: int
    target_load: Optional[float] = 0.2
    memory_mb: Optional[int] = 1

@app.post("/load-test")
async def load_test(postdata: LoadtestPostData):
    """
    API to load test the microservice.
    """

    # Authentication
    secret_token = postdata.secret_token
    if secret_token != APP_SECRET_TOKEN:
        return JSONResponse({
            "status": "authentication_failure",
            "message": "Authentication Failed! Please provide a valid secret token."
        }, status_code=401)

    _start_time = time.time()

    # Gather variables
    job_id = str(uuid.uuid4()).replace("-","")

    duration_s = postdata.duration_s
    target_load = postdata.target_load
    memory_mb = max( min(postdata.memory_mb, 1000), 1)

    # Prepare
    response_data = {
        "_worker_id": WORKER_ID,
        "_version": app.version,
        "job_id": job_id,
        "handle_id": postdata.handle_id,
        "metadata": postdata.metadata,
        "params": {
            "duration_s": duration_s,
            "target_load": target_load,
            "memory_mb": memory_mb
        },
        "datetime": datetime.utcnow().strftime(FORMAT_UTC_DATETIME),
    }

    # --- Load Server ---
    result = {}

    # Load memory
    with open(PATH_SAMPLE_FILE, "r") as f:
        content = f.read()

    mem_object = ""
    n_iter = memory_mb // SAMPLE_FILE_SIZE_MB
    for i in range(n_iter):
        mem_object += content
    result["memory_used_mb"] = sys.getsizeof(mem_object) / (1024*1024)

    # Load CPU
    try:
        load_all_cores(duration_s=duration_s, target_load=target_load)
        cpu_result = "Done"
    except:
        cpu_result = "Failed"
    result["cpu_result"] = cpu_result

    # --- /Load Server ---

    # Completed
    time_taken_ms = (time.time()-_start_time)*1000.0

    # Cleanup
    del mem_object

    # Finalize response
    response_data['status'] = "ok"
    response_data['result'] = result
    response_data['time_taken_ms'] = time_taken_ms

    # Return
    return JSONResponse(response_data)


logger.info(f"Worker={WORKER_ID} - Done! Service initialized successfully.")
logger.info(f"Worker={WORKER_ID} - Service Ready!")
# ----- Create Server -----



# ----- Main -----
if __name__ == "__main__":
    import uvicorn
    print("Running server from python main...")
    print(f"App secret token='{APP_SECRET_TOKEN}'")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_config="log_config.json")