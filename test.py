import unittest
import urllib.request
import urllib.error
import urllib.parse
import json
import base64
import subprocess
import logging
import os
import time
import sys


# Set Logger
logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s|TEST|%(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


# Get Environment variables
PORT = int(os.getenv('APP_PORT', '7000'))


# Global vars
BASE_URL = f"http://127.0.0.1:{PORT}"
SERVER_PID = None


# ---------- Helpers ----------
def sendLoadtestRequest(payload):
    """
    Method to send loadtest request to the server.
    :param payload: Json data
    """
    url = f"{BASE_URL}/load-test"
    postdata = json.dumps(payload).encode('ascii')
    headers = {'content-type': 'application/json'}

    request = urllib.request.Request(url, postdata, headers)
    response = urllib.request.urlopen(request)

    return request, response


# ---------- /Helpers ----------



class TestLoadtestService(unittest.TestCase):
    """
    Class to run test on Load test service
    """

    @classmethod
    def setUpClass(cls):
        """
        Method to setup scenario for test case.
        """

        global SERVER_PID

        # Check if server is allready running
        is_server_running = False

        try:
            response = urllib.request.urlopen(f"{BASE_URL}/")
            logging.info(f"Using server already running at {BASE_URL}.")
        except urllib.error.URLError:
            # Server is NOT running; Start server
            cmd = f"{sys.executable} microapp.py"
            env_vars = os.environ.copy()

            logging.info(f"No server running at {BASE_URL}.")
            logging.info(f"Starting a development server:\n\t{cmd}\n")
            proc_server = subprocess.Popen(
                cmd,
                env=env_vars,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            SERVER_PID = proc_server.pid
            time.sleep(10)
            logging.info(f"Success! Server started with PID={SERVER_PID}.")

        logging.info("Running all tests...\n")


    @classmethod
    def tearDownClass(cls):
        global SERVER_PID

        if SERVER_PID:
            logging.info(f"Stopping server...")
            try:
                # 2  - Ctrl+C; SIGINT
                # 15 - SIGTERM
                # 9  - SIGKILL

                # Kill Server
                response = urllib.request.urlopen(f"{BASE_URL}/")
                data = json.loads(response.read())
                pid = data['pid']
                os.kill(pid, 15)

                # Kill uvicorn (SERVER_PID is pid of uvicorn)
                os.kill(SERVER_PID, 15)

                logging.info("Done!")
            except Exception as ex:
                logging.error(f"Unable to kill server process with PID={SERVER_PID}:\n{ex}")
                logging.info("Ignoring!")


    def test_service(self):
        """
        Test to check if service is live or not.
        """
        url = f"{BASE_URL}/"
        response = urllib.request.urlopen(url)

        # Check status code
        self.assertTrue( (200 <= response.status <= 299), "Service did not return HTTP 200." )

        # Read response
        try:
            response_data = json.loads( response.read())

            self.assertEqual( response_data['status'], 'ok', "Server status is not 'ok'." )
        except json.decoder.JSONDecodeError:
            raise AssertionError("Server did not return a valid json response.")


    def test_health(self):
        """
        Test to check health of the service.
        """

        url = f"{BASE_URL}/health"
        response = urllib.request.urlopen(url)

        # Check status code
        self.assertTrue((200 <= response.status <= 299), "Health did not return HTTP 200.")

        # Read response
        try:
            response_data = json.loads(response.read())

            self.assertEqual(response_data['status'], 'ok', "Health is not 'ok'.")
        except json.decoder.JSONDecodeError:
            raise AssertionError("Server did not return a valid json response.")


    def test_loadtest_url(self):
        """
        Test to check load test endpoint.
        """

        payload = {
            "secret_token": "secret",
            "handle_id": "py-test-0001",
            "metadata": {
                "some-key": "some-value"
            },
            "duration_s": 2,
            "target_load": 0.2,
            "memory_mb": 5
        }
        request, response = sendLoadtestRequest(payload=payload)

        # Check status code
        self.assertTrue((200 <= response.status <= 299), "URL did not return HTTP 200.")

        # Read response
        try:
            response_data = json.loads(response.read())

            self.assertEqual(response_data['status'], 'ok', "Response status is not 'ok'.")
        except json.decoder.JSONDecodeError:
            raise AssertionError("Server did not return a valid json response.")


if __name__ == '__main__':
    unittest.main(verbosity=2)