# Wrist X-Ray Fracture Analysis

A FastAPI service and Streamlit interface for analyzing wrist radiographs with a trained Ultralytics YOLO model.

## Requirements

- Docker Desktop with Docker Compose, for the containerized setup.
- Python 3.14 and pip, for local setup. The Docker image uses Python 3.14.
- The trained model weights at `modelo/yolo_model/best.pt`.

The API loads `best.pt` when it starts. Keep the weights file in that exact location. The Docker build copies the `modelo` directory into the image.

## Run with Docker

From the project root, build and start both the API and frontend:

```powershell
docker compose up --build
```

Open the Streamlit interface at <http://localhost:8501>. The FastAPI interactive documentation is at <http://localhost:8000/docs>.

To stop the services, press `Ctrl+C`, then run:

```powershell
docker compose down
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
streamlit run app.py
```

Open the interface at <http://localhost:8501>. The local frontend defaults to the API at `http://127.0.0.1:8000/predictAI/multiple`. API documentation is available at <http://127.0.0.1:8000/docs>.

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
python -m streamlit run app.py
```

Open the interface at <http://localhost:8501>. The frontend connects to the API at `http://127.0.0.1:8000` by default.

## API

- `POST /predictAI`: analyze one image using multipart form data with the `file` field.
- `POST /predictAI/multiple`: analyze 1 to 20 images using multipart form data with repeated `files` fields.

Images must be JPEG or PNG and no larger than 10 MB each. Successful results include the prediction, the number of detected fractures, per-detection confidence and bounding boxes, and a base64-encoded annotated image. The model runs at image size 1024 with a detection confidence threshold of 0.25.

## Troubleshooting

- **Model file not found:** verify `modelo/yolo_model/best.pt` exists before starting the API or building the image.
- **Frontend cannot connect:** start the API first and check that port 8000 is available. With Docker Compose, start both services using `docker compose up --build`.
- **Dependency installation fails:** confirm Python 3.14 is installed and that the virtual environment is active before installing `requirements.txt`.