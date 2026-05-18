FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libopencv-dev \
    pkg-config \
    python3-opencv \
    && opencv_version \
    && pkg-config --modversion opencv4 \
    && python3 -c "import cv2; print(cv2.__version__)" \
    && rm -rf /var/lib/apt/lists/*

COPY scripts/generate-mask.py /usr/local/bin/opencv-generate-mask

RUN chmod +x /usr/local/bin/opencv-generate-mask

WORKDIR /data

CMD ["opencv_version"]
