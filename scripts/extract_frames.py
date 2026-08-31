# ============================================================
# extract_frames.py
# Lip Reading / Visual Speech Recognition Project
#
# PHASE 1.5
# Video -> Individual Frames + Metadata
# ============================================================

from pathlib import Path
from datetime import datetime
import argparse
import csv
import json
import sys
import cv2


# ============================================================
# PROJECT PATH
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

DEFAULT_VIDEO_DIR = (
    PROJECT_DIR
    / "dataset"
    / "raw_videos"
)

DEFAULT_FRAME_DIR = (
    PROJECT_DIR
    / "dataset"
    / "frames"
)


# ============================================================
# CONFIGURATION
# ============================================================

SUPPORTED_VIDEO_EXTENSIONS = {
    ".webm",
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".mpeg",
    ".mpg",
}

DEFAULT_IMAGE_EXTENSION = ".jpg"

# JPG 95 ช่วยลด compression artifact
# แต่ขนาดไฟล์ยังไม่ใหญ่เท่า PNG
JPEG_QUALITY = 95


# ============================================================
# LOGGER
# ============================================================

def log(message: str):

    print(message, flush=True)


# ============================================================
# FIND VIDEO FILES
# ============================================================

def discover_videos(video_dir: Path):

    if not video_dir.exists():

        raise FileNotFoundError(
            f"ไม่พบโฟลเดอร์วิดีโอ:\n{video_dir}"
        )

    videos = []

    for path in video_dir.iterdir():

        if (
            path.is_file()
            and
            path.suffix.lower()
            in SUPPORTED_VIDEO_EXTENSIONS
        ):
            videos.append(path)

    videos.sort()

    return videos


# ============================================================
# READ VIDEO INFORMATION
# ============================================================

def get_video_info(video_path: Path):

    cap = cv2.VideoCapture(
        str(video_path)
    )

    if not cap.isOpened():

        raise RuntimeError(
            f"ไม่สามารถเปิดวิดีโอได้: {video_path}"
        )

    fps = float(
        cap.get(
            cv2.CAP_PROP_FPS
        )
    )

    width = int(
        cap.get(
            cv2.CAP_PROP_FRAME_WIDTH
        )
    )

    height = int(
        cap.get(
            cv2.CAP_PROP_FRAME_HEIGHT
        )
    )

    frame_count = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    duration = (
        frame_count / fps
        if fps > 0
        else 0
    )

    cap.release()

    return {
        "fps": fps,
        "width": width,
        "height": height,
        "frame_count": frame_count,
        "duration": duration,
    }


# ============================================================
# SAVE JSON
# ============================================================

def save_json(
    path: Path,
    data: dict
):

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# FRAME QUALITY INFORMATION
#
# ยังไม่ reject frame
# เราเก็บค่าไว้ก่อน เพื่อให้ Phase QA
# เลือกตัดทีหลังได้
# ============================================================

def calculate_frame_quality(frame):

    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )

    # ----------------------------
    # Blur score
    # ----------------------------

    blur_score = float(
        cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()
    )

    # ----------------------------
    # Brightness
    # ----------------------------

    brightness = float(
        gray.mean()
    )

    return (
        round(
            blur_score,
            3
        ),
        round(
            brightness,
            3
        )
    )


# ============================================================
# EXTRACT ONE VIDEO
# ============================================================

def extract_video_frames(
    video_path: Path,
    frame_root: Path,
    frame_stride: int = 1,
    overwrite: bool = False,
    calculate_quality: bool = True,
    max_frames=None
):

    video_id = video_path.stem

    video_output_dir = (
        frame_root
        / video_id
    )

    video_output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    metadata_csv = (
        video_output_dir
        / "frames_metadata.csv"
    )

    video_metadata_json = (
        video_output_dir
        / "video_metadata.json"
    )

    done_file = (
        video_output_dir
        / ".complete"
    )

    # ========================================================
    # RESUME / SKIP
    # ========================================================

    if (
        done_file.exists()
        and
        not overwrite
    ):

        log(
            f"SKIP: {video_id} "
            "(เคย extract เสร็จแล้ว)"
        )

        return

    # ========================================================
    # VIDEO INFO
    # ========================================================

    info = get_video_info(
        video_path
    )

    fps = info["fps"]
    width = info["width"]
    height = info["height"]
    frame_count = info["frame_count"]
    duration = info["duration"]

    log("")
    log("=" * 70)
    log(f"VIDEO : {video_id}")
    log("=" * 70)

    log(
        f"File       : {video_path.name}"
    )

    log(
        f"Resolution : {width}x{height}"
    )

    log(
        f"FPS        : {fps:.3f}"
    )

    log(
        f"Frames     : {frame_count}"
    )

    log(
        f"Duration   : {duration:.2f} sec"
    )

    log(
        f"Stride     : {frame_stride}"
    )

    log("=" * 70)

    # ========================================================
    # SAVE VIDEO METADATA
    # ========================================================

    video_metadata = {

        "video_id":
            video_id,

        "source_file":
            str(
                video_path.resolve()
            ),

        "original_filename":
            video_path.name,

        "fps":
            round(
                fps,
                6
            ),

        "width":
            width,

        "height":
            height,

        "frame_count":
            frame_count,

        "duration_seconds":
            round(
                duration,
                6
            ),

        "frame_stride":
            frame_stride,

        "created_at":
            datetime.now().isoformat()
    }

    save_json(
        video_metadata_json,
        video_metadata
    )

    # ========================================================
    # OPEN VIDEO
    # ========================================================

    cap = cv2.VideoCapture(
        str(video_path)
    )

    if not cap.isOpened():

        raise RuntimeError(
            f"ไม่สามารถเปิดวิดีโอได้: "
            f"{video_path}"
        )

    # ========================================================
    # CSV
    # ========================================================

    csv_file = open(
        metadata_csv,
        "w",
        newline="",
        encoding="utf-8-sig"
    )

    writer = csv.writer(
        csv_file
    )

    writer.writerow([
        "video_id",
        "source_frame_index",
        "saved_frame_index",
        "timestamp_seconds",
        "filename",
        "width",
        "height",
        "blur_score",
        "brightness",
    ])

    # ========================================================
    # FRAME LOOP
    # ========================================================

    source_frame_index = 0
    saved_frame_index = 0

    try:

        while True:

            ret, frame = cap.read()

            if not ret:
                break

            # ------------------------------------------------
            # FRAME STRIDE
            # ------------------------------------------------

            if (
                source_frame_index
                % frame_stride
                != 0
            ):

                source_frame_index += 1
                continue

            # ------------------------------------------------
            # Timestamp
            # ------------------------------------------------

            if fps > 0:

                timestamp_seconds = (
                    source_frame_index
                    / fps
                )

            else:

                timestamp_seconds = (
                    cap.get(
                        cv2.CAP_PROP_POS_MSEC
                    )
                    / 1000.0
                )

            # ------------------------------------------------
            # Filename
            # ------------------------------------------------

            frame_filename = (
                f"frame_"
                f"{source_frame_index:08d}"
                f"{DEFAULT_IMAGE_EXTENSION}"
            )

            frame_path = (
                video_output_dir
                / frame_filename
            )

            # ------------------------------------------------
            # Save frame
            # ------------------------------------------------

            save_success = cv2.imwrite(

                str(
                    frame_path
                ),

                frame,

                [
                    cv2.IMWRITE_JPEG_QUALITY,
                    JPEG_QUALITY
                ]

            )

            if not save_success:

                log(
                    f"WARNING: "
                    f"บันทึกไม่ได้ "
                    f"{frame_filename}"
                )

                source_frame_index += 1

                continue

            # ------------------------------------------------
            # Frame QA Information
            # ------------------------------------------------

            blur_score = ""
            brightness = ""

            if calculate_quality:

                (
                    blur_score,
                    brightness
                ) = calculate_frame_quality(
                    frame
                )

            # ------------------------------------------------
            # CSV ROW
            # ------------------------------------------------

            frame_height = (
                frame.shape[0]
            )

            frame_width = (
                frame.shape[1]
            )

            writer.writerow([

                video_id,

                source_frame_index,

                saved_frame_index,

                round(
                    timestamp_seconds,
                    6
                ),

                frame_filename,

                frame_width,

                frame_height,

                blur_score,

                brightness,

            ])

            # ------------------------------------------------
            # Progress
            # ------------------------------------------------

            saved_frame_index += 1

            if (
                saved_frame_index
                % 500
                == 0
            ):

                percent = (

                    (
                        source_frame_index
                        /
                        max(
                            frame_count,
                            1
                        )
                    )

                    * 100

                )

                log(
                    f"{video_id} | "
                    f"saved "
                    f"{saved_frame_index:,} "
                    f"frames | "
                    f"{percent:.1f}%"
                )

            # ------------------------------------------------
            # Max frame option
            # ------------------------------------------------

            if (
                max_frames is not None
                and
                saved_frame_index
                >= max_frames
            ):
                break

            source_frame_index += 1

    finally:

        cap.release()

        csv_file.close()

    # ========================================================
    # COMPLETE MARKER
    # ========================================================

    complete_data = {

        "video_id":
            video_id,

        "saved_frames":
            saved_frame_index,

        "last_source_frame":
            source_frame_index,

        "completed_at":
            datetime.now().isoformat()

    }

    save_json(
        done_file,
        complete_data
    )

    log("")
    log(
        f"DONE : {video_id}"
    )

    log(
        f"Saved frames : "
        f"{saved_frame_index:,}"
    )

    log(
        f"Output : "
        f"{video_output_dir}"
    )

    log("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(

        description=(
            "Extract video frames "
            "for Lip Reading dataset"
        )

    )

    parser.add_argument(

        "--video-dir",

        type=str,

        default=str(
            DEFAULT_VIDEO_DIR
        ),

        help=(
            "Directory containing "
            "source videos"
        )

    )

    parser.add_argument(

        "--output-dir",

        type=str,

        default=str(
            DEFAULT_FRAME_DIR
        ),

        help=(
            "Output directory "
            "for extracted frames"
        )

    )

    parser.add_argument(

        "--stride",

        type=int,

        default=1,

        help=(
            "Save every N frames. "
            "Default=1 saves every frame."
        )

    )

    parser.add_argument(

        "--overwrite",

        action="store_true",

        help=(
            "Re-extract videos "
            "already marked complete"
        )

    )

    parser.add_argument(

        "--no-quality",

        action="store_true",

        help=(
            "Do not calculate "
            "blur/brightness"
        )

    )

    parser.add_argument(

        "--max-frames",

        type=int,

        default=None,

        help=(
            "Maximum frames per video. "
            "Useful for testing."
        )

    )

    args = parser.parse_args()

    # ========================================================
    # Validate
    # ========================================================

    if args.stride <= 0:

        raise ValueError(
            "--stride ต้องมากกว่า 0"
        )

    video_dir = Path(
        args.video_dir
    ).resolve()

    output_dir = Path(
        args.output_dir
    ).resolve()

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # ========================================================
    # Discover
    # ========================================================

    videos = discover_videos(
        video_dir
    )

    log("")
    log("=" * 70)
    log("LIP READING — FRAME EXTRACTION")
    log("=" * 70)

    log(
        f"Video directory : "
        f"{video_dir}"
    )

    log(
        f"Frame directory : "
        f"{output_dir}"
    )

    log(
        f"Videos found    : "
        f"{len(videos)}"
    )

    log(
        f"Frame stride    : "
        f"{args.stride}"
    )

    log("=" * 70)

    if not videos:

        log(
            "ไม่พบไฟล์วิดีโอ"
        )

        return

    # ========================================================
    # PROCESS ALL VIDEOS
    # ========================================================

    success_count = 0
    failed_count = 0

    for video_path in videos:

        try:

            extract_video_frames(

                video_path=
                    video_path,

                frame_root=
                    output_dir,

                frame_stride=
                    args.stride,

                overwrite=
                    args.overwrite,

                calculate_quality=
                    not args.no_quality,

                max_frames=
                    args.max_frames

            )

            success_count += 1

        except Exception as e:

            failed_count += 1

            log("")
            log(
                f"ERROR : "
                f"{video_path.name}"
            )

            log(
                str(e)
            )

    # ========================================================
    # SUMMARY
    # ========================================================

    log("")
    log("=" * 70)
    log("FRAME EXTRACTION FINISHED")
    log("=" * 70)

    log(
        f"Success : "
        f"{success_count}"
    )

    log(
        f"Failed  : "
        f"{failed_count}"
    )

    log("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print(
            "\nหยุดการทำงานโดยผู้ใช้"
        )

        sys.exit(130)