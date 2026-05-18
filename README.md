# docker-opencv

Docker image for running distro-packaged OpenCV from an Ubuntu 24.04 container.

This image is intentionally conservative: it uses Ubuntu's maintained `libopencv-dev` and `python3-opencv` packages instead of building OpenCV from source. It provides OpenCV command-line smoke checks, C/C++ development headers and libraries, `pkg-config` metadata, and Python `cv2` bindings.

This image does not include Node.js or `opencv4nodejs`.

## Build

```bash
docker build -t docker-opencv:test .
```

The release image path configured by `deploy.json` is:

```text
australia-southeast1-docker.pkg.dev/cognitive-code/opencv/main
```

## Smoke Test

The default command prints the installed OpenCV version:

```bash
docker run --rm docker-opencv:test
```

You can also check the C/C++ package metadata and Python binding:

```bash
docker run --rm docker-opencv:test pkg-config --modversion opencv4
docker run --rm docker-opencv:test python3 -c "import cv2; print(cv2.__version__)"
```

## Inspect An Image With Python

Mount the directory containing your files as `/data`, then reference paths inside `/data`:

```bash
docker run --rm \
  -v "$PWD:/data:ro" \
  docker-opencv:test \
  python3 -c "import cv2; img = cv2.imread('/data/example.png'); print(img.shape if img is not None else 'unreadable')"
```

For a file in another directory:

```bash
IMAGE_DIR="$HOME/cognitiveEarth/view-utilities/test/output/downloads/virtual-mnsw-pipeline/all/pngs-pseudo-lvl5/buffers_all_POSITION/20"
IMAGE_FILE="pseudo_lvl5_from_lvl6_117_43_to_117_44.contentLength.png"

docker run --rm \
  -v "$IMAGE_DIR:/data:ro" \
  docker-opencv:test \
  python3 -c "import cv2; img = cv2.imread('/data/$IMAGE_FILE'); print(img.shape if img is not None else 'unreadable')"
```

## Generate A Mask

The image includes `opencv-generate-mask`, a small CLI for generating the accepted hole-preserving mask. Its defaults are:

```text
threshold=8
kernel-size=5
close-iterations=2
preserve-holes=2
```

Run it by mounting the image directory as `/data`:

```bash
IMAGE_DIR="$HOME/cognitiveEarth/view-utilities/test/output/downloads/virtual-mnsw-pipeline/all/pngs-pseudo-lvl5-lvl14px/buffers_all_POSITION/16"
IMAGE_FILE="pseudo_lvl5_1px_per_lvl14_from_z16_lvl6_117_43_to_117_44.contentLength.png"
MASK_FILE="${IMAGE_FILE%.png}.mask.preserve-2-holes.threshold8.close5x5.iter2.png"

docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$IMAGE_DIR:/data" \
  docker-opencv:test \
  opencv-generate-mask "/data/$IMAGE_FILE" "/data/$MASK_FILE"
```

The equivalent explicit form is:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$IMAGE_DIR:/data" \
  docker-opencv:test \
  opencv-generate-mask \
    --threshold 8 \
    --kernel-size 5 \
    --close-iterations 2 \
    --preserve-holes 2 \
    "/data/$IMAGE_FILE" \
    "/data/$MASK_FILE"
```
