# ==========================================
# youtube_download.py
# Lip Reading Project
# Download YouTube -> WEBM
# ==========================================

from pathlib import Path
import yt_dlp


# =========================================================
# Configuration
# =========================================================

OUTPUT_DIR = Path(
    r"D:\Face_detection\dataset\raw_videos"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================
# Find Next Video Number
# =========================================================

def get_next_video_number(output_dir):

    numbers = []

    # รองรับทั้ง .webm และ .mp4
    for file in output_dir.iterdir():

        if not file.is_file():
            continue

        name = file.stem

        if not name.startswith("video"):
            continue

        number = name[5:]

        if number.isdigit():

            numbers.append(
                int(number)
            )

    if not numbers:

        return 1

    return max(numbers) + 1


# =========================================================
# Download YouTube Video
# =========================================================

def download_youtube_video(
    youtube_url,
    output_dir
):

    video_number = get_next_video_number(
        output_dir
    )

    video_name = (
        f"video{video_number:03d}"
    )

    output_template = (
        output_dir /
        f"{video_name}.%(ext)s"
    )

    print()
    print("=" * 70)
    print("YouTube Downloader")
    print("=" * 70)

    print(
        f"URL    : {youtube_url}"
    )

    print(
        f"Output : {output_dir / (video_name + '.webm')}"
    )

    print("=" * 70)

    # =====================================================
    # yt-dlp Configuration
    # =====================================================

    ydl_opts = {

        # เลือก video + audio ที่เป็น WEBM
        "format":
            "bestvideo[ext=webm]+"
            "bestaudio[ext=webm]/"
            "best[ext=webm]",

        # ต้องการ WEBM
        "merge_output_format":
            "webm",

        # ชื่อไฟล์
        "outtmpl":
            str(output_template),

        # ดาวน์โหลดเฉพาะวิดีโอ ไม่เอา playlist
        "noplaylist":
            True,

        # ไม่ overwrite ไฟล์เดิม
        "overwrites":
            False,

        # Retry
        "retries":
            5,

        "fragment_retries":
            5,

        "socket_timeout":
            30,

        # แสดง progress
        "progress":
            True
    }

    # =====================================================
    # Download
    # =====================================================

    try:

        with yt_dlp.YoutubeDL(
            ydl_opts
        ) as ydl:

            info = ydl.extract_info(
                youtube_url,
                download=True
            )

        # =================================================
        # Find Downloaded WEBM
        # =================================================

        expected_file = (
            output_dir /
            f"{video_name}.webm"
        )

        if expected_file.exists():

            final_path = expected_file

        else:

            possible_files = list(
                output_dir.glob(
                    f"{video_name}.*"
                )
            )

            webm_files = [

                f

                for f in possible_files

                if f.suffix.lower() == ".webm"

            ]

            if not webm_files:

                raise FileNotFoundError(
                    "ไม่พบไฟล์ .webm หลังดาวน์โหลด"
                )

            final_path = webm_files[0]

        # =================================================
        # Metadata
        # =================================================

        title = info.get(
            "title",
            "Unknown"
        )

        duration = info.get(
            "duration",
            0
        )

        uploader = info.get(
            "uploader",
            "Unknown"
        )

        # =================================================
        # Success
        # =================================================

        print()
        print("=" * 70)
        print("DOWNLOAD SUCCESS")
        print("=" * 70)

        print(
            f"Video ID : {video_name}"
        )

        print(
            f"Title    : {title}"
        )

        print(
            f"Uploader : {uploader}"
        )

        print(
            f"Duration : {duration} sec"
        )

        print(
            f"Format   : {final_path.suffix}"
        )

        print(
            f"File     : {final_path}"
        )

        print("=" * 70)

        return final_path

    except Exception as e:

        print()
        print("=" * 70)
        print("DOWNLOAD FAILED")
        print("=" * 70)

        print(
            f"Error: {e}"
        )

        print("=" * 70)

        return None


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("Lip Reading — YouTube Downloader")
    print("=" * 70)

    print(
        f"Save directory:"
    )

    print(
        OUTPUT_DIR
    )

    print("=" * 70)

    youtube_url = input(
        "ใส่ YouTube URL: "
    ).strip()

    # -----------------------------------------------------
    # Validate URL
    # -----------------------------------------------------

    if not youtube_url:

        print(
            "❌ ไม่ได้รับ YouTube URL"
        )

        raise SystemExit(1)

    # -----------------------------------------------------
    # Download
    # -----------------------------------------------------

    download_youtube_video(
        youtube_url,
        OUTPUT_DIR
    )