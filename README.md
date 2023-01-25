# MicroApp
A python based micro app for testing

## Docker
- Build development docker
    ```shell
    docker build -t metaoptima/microapp .
    ```

- Run
    ```shell
    docker run --name microapp_test -e APP_SECRET_TOKEN=my-secret -p 9001:7000 -d metaoptima/microapp
    ```

- Login inside the container
    ```shell
    docker exec -it microapp_test bash
    ```

- Run test
    ```shell
    docker run -it metaoptima/microapp python test.py
    ```

## Environment Variables
```
APP_SECRET_TOKEN='<some-secret-token>'

# Optional
APP_PORT=8111
```

## Sample Test Case

- Endpoint: `/load-test`
  - Test Case 1
    ```json
    {
      "secret_token": "secret",
      "handle_id": "test-0001",
      "metadata": {
        "some-key": "some-val"
      },
      "duration_s": 10,
      "target_load": 0.2,
      "memory_mb": 5
    }
    ```
  - Test Case 2
    ```json
    {
      "secret_token": "secret",
      "handle_id": "test-0002",
      "metadata": {},
      "duration_s": 20,
      "memory_mb": 100
    }
    ```
    
## TODO
- Kill Signal handling

## Author
Gagandeep SIngh