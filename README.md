# Wrist X-Ray Fracture Analysis

A FastAPI service and Streamlit interface for analyzing wrist radiographs with a trained Ultralytics YOLO model. The API accepts multiple images in one request and returns per-image predictions and error details.

## Requirements

- Docker Desktop with Docker Compose, for the containerized setup.
- Python 3.14 and pip, for local setup. The Docker image uses Python 3.14.
- The trained model weights at `Modelos/best.pt`.

The API loads `best.pt` when it starts. Keep the weights file at `Modelos/best.pt`. The Docker image copies the `Src` and `Modelos` directories into the container.

## Run with Docker

From the project root, build and start both the API and frontend using the Compose file in `Docker`:

```powershell
docker compose -f Docker/docker-compose.yml up --build
```

Open the Streamlit interface at <http://localhost:8501>. The FastAPI interactive documentation is at <http://localhost:8000/docs>.

To stop the services, press `Ctrl+C`, then run:

```powershell
docker compose -f Docker/docker-compose.yml down
```

## Run locally without Docker

Open two PowerShell terminals in the project root. Create and activate a virtual environment in the first terminal, then install the dependencies:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, allow scripts for this terminal session and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Start the API in the first terminal:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

In the second terminal, activate the same environment and start Streamlit:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run Src\View\app.py
```

Open the interface at <http://localhost:8501>. The frontend defaults to `http://127.0.0.1:8000/predictAI`. Set the `API_URL` environment variable if the API is running at a different address. API documentation is available at <http://127.0.0.1:8000/docs>.

### Linux

Install Python 3.14 and pip. On Debian or Ubuntu, also install the OpenCV system libraries:

```bash
sudo apt-get update
sudo apt-get install -y libgl1 libglib2.0-0
```

From the project root, create and activate a virtual environment, then install the dependencies:

```bash
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Start the API in the first terminal:

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal, go to the project root, activate the same environment, and start the frontend:

```bash
source .venv/bin/activate
python -m streamlit run Src/View/app.py
```

Open the interface at <http://localhost:8501>. The frontend defaults to `http://127.0.0.1:8000/predictAI`.

## API

- `POST /predictAI`: analyze 1 to 20 images using multipart form data with repeated `files` fields.

The Streamlit interface accepts JPEG and PNG images, with a maximum of 20 images per analysis. Each image must be no larger than 5 MB. The response contains an overall `status`, image and success/error counts, and a `resultados` list. Successful items include `sucesso`, the prediction, the number of detected fractures, per-detection confidence and bounding boxes, and a base64-encoded annotated image. Failed items include `sucesso: false`, an HTTP `status_code`, an `erro` message, and the source `file` name. The model runs at image size 1024 with a detection confidence threshold of 0.25.

## Troubleshooting

- **Model file not found:** verify `Modelos/best.pt` exists before starting the API or building the image.
- **Frontend cannot connect:** start the API first and check that port 8000 is available. With Docker Compose, start both services using `docker compose -f Docker/docker-compose.yml up --build`.
- **Image exceeds the limit:** reduce the file size to 5 MB or less and upload it again.
- **Dependency installation fails:** confirm Python 3.14 is installed and that the virtual environment is active before installing `requirements.txt`.