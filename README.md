# FastAPI File Server

Small FastAPI app with upload and download endpoints.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 4443
```

The server starts at `http://127.0.0.1:4443`.
Using port `4443` does not enable HTTPS by itself. This app still serves plain HTTP unless you add TLS separately.
Uploaded files are stored in the local `files/` directory, which the app creates automatically on startup.
Set `FILES_DIR` to store uploads somewhere else.

For a long-running deployment, use Uvicorn without `--reload`, or run it as a `systemd` service.

## Docker

Build the image:

```bash
docker build -t file-server:latest .
```

Preferred deployment with Docker Compose:

```bash
docker compose up -d
```

Inside the container, uploaded files are stored in `/data` by default.

The included [`compose.yaml`](compose.yaml) maps `/srv/file-server-data` on the host to `/data` in the container.

If you prefer a one-off container command instead:

```bash
docker run -d \
  --name file-server \
  --restart unless-stopped \
  -p 4443:4443 \
  -v /srv/file-server-data:/data \
  file-server:latest
```

Move the built image to another server:

```bash
docker save -o file-server-image.tar file-server:latest
```

On the production server:

```bash
docker load -i file-server-image.tar
docker compose up -d
```

Useful environment variables:

- `PORT` changes the listening port inside the container
- `FILES_DIR` changes where uploads are stored

Health check endpoint:

- `GET /healthz`

## Endpoints

- `GET /` basic API info
- `GET /healthz` health check
- `GET /files` list uploaded files
- `POST /upload` upload a file
- `GET /download/{filename}` download a file
- `GET /download?file={filename}` download a file
- `GET /files/{filename}` legacy download alias

## Examples

Upload:

```bash
curl -F "file=@./example.txt" http://127.0.0.1:4443/upload
```

Overwrite an existing file:

```bash
curl -F "file=@./example.txt" "http://127.0.0.1:4443/upload?overwrite=true"
```

Download:

```bash
curl -O http://127.0.0.1:4443/download/example.txt
```

Download with query string:

```bash
curl -O "http://127.0.0.1:4443/download?file=example.txt"
```

## Run As A systemd Service

Example service file:

```ini
[Unit]
Description=FastAPI File Server
After=network.target

[Service]
User=mark
Group=mark
WorkingDirectory=/home/mark/pycharm_projects/file_server
ExecStart=/home/mark/pycharm_projects/file_server/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 4443
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Save it as `/etc/systemd/system/file-server.service`.

Reload `systemd`, enable the service at boot, and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now file-server.service
```

Check service status:

```bash
sudo systemctl status file-server.service
```

View logs:

```bash
sudo journalctl -u file-server.service -f
```

If you deploy new code or dependencies, restart the service:

```bash
sudo systemctl restart file-server.service
```
