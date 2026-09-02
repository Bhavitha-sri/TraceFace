import os
import sys
import json
import tempfile

import cv2
import requests
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

ENV_FILE = os.path.join(
    BASE_DIR,
    ".env"
)

RESULTS_FILE = os.path.join(
    BASE_DIR,
    "data",
    "web_results.json"
)

SERPAPI_IMAGE_URL = (
    "https://serpapi.com/image"
)

SERPAPI_SEARCH_URL = (
    "https://serpapi.com/search"
)

MAX_UPLOAD_SIZE = 500 * 1024


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv(
    ENV_FILE
)

SERPAPI_API_KEY = os.getenv(
    "SERPAPI_API_KEY"
)


# ============================================================
# VALIDATE API KEY
# ============================================================

if not SERPAPI_API_KEY:

    raise ValueError(
        "SERPAPI_API_KEY is missing from .env"
    )


# ============================================================
# PREPARE IMAGE
# ============================================================

def prepare_image(
    image_path
):
    """
    SerpApi's Image API accepts JPG/JPEG, PNG, and WebP,
    with a maximum file size of 500 KB.

    If the original image is already within the limit,
    use it directly.

    Otherwise create a temporary compressed JPEG.
    """

    if not os.path.isfile(
        image_path
    ):

        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )


    original_size = os.path.getsize(
        image_path
    )


    if original_size <= MAX_UPLOAD_SIZE:

        return image_path, None


    # --------------------------------------------------------
    # Read image
    # --------------------------------------------------------

    image = cv2.imread(
        image_path
    )

    if image is None:

        raise ValueError(
            "OpenCV could not read the image."
        )


    # --------------------------------------------------------
    # Create temporary compressed image
    # --------------------------------------------------------

    temporary_file = tempfile.NamedTemporaryFile(
        suffix=".jpg",
        delete=False
    )

    temporary_path = temporary_file.name

    temporary_file.close()


    # Start with current dimensions
    height, width = image.shape[:2]

    quality = 85


    # Try progressively smaller images until
    # we are below SerpApi's 500 KB limit.
    success = False


    for attempt in range(12):

        encoded_ok, encoded = cv2.imencode(
            ".jpg",
            image,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                quality
            ]
        )


        if not encoded_ok:

            continue


        with open(
            temporary_path,
            "wb"
        ) as file:

            file.write(
                encoded.tobytes()
            )


        current_size = os.path.getsize(
            temporary_path
        )


        if current_size <= (
            MAX_UPLOAD_SIZE - 20 * 1024
        ):

            success = True
            break


        # Reduce dimensions
        width = int(
            width * 0.85
        )

        height = int(
            height * 0.85
        )


        if width < 300:
            width = 300

        if height < 300:
            height = 300


        image = cv2.resize(
            image,
            (width, height),
            interpolation=cv2.INTER_AREA
        )


        if quality > 55:

            quality -= 5


    if not success:

        try:

            os.remove(
                temporary_path
            )

        except OSError:

            pass


        raise ValueError(
            "Could not compress image below SerpApi's 500 KB limit."
        )


    return (
        temporary_path,
        temporary_path
    )


# ============================================================
# UPLOAD IMAGE TO SERPAPI
# ============================================================

def upload_image(
    image_path
):

    print()
    print(
        "Uploading image to SerpApi..."
    )


    with open(
        image_path,
        "rb"
    ) as image_file:

        response = requests.post(

            SERPAPI_IMAGE_URL,

            data={
                "api_key":
                    SERPAPI_API_KEY
            },

            files={
                "image":
                    (
                        os.path.basename(
                            image_path
                        ),
                        image_file,
                        "application/octet-stream"
                    )
            },

            timeout=60
        )


    try:

        data = response.json()

    except ValueError:

        raise RuntimeError(
            "SerpApi returned a non-JSON response."
        )


    if response.status_code != 200:

        error_message = data.get(
            "error",
            f"HTTP {response.status_code}"
        )

        raise RuntimeError(
            f"SerpApi image upload failed: {error_message}"
        )


    if "error" in data:

        raise RuntimeError(
            f"SerpApi image upload failed: {data['error']}"
        )


    image_id = data.get(
        "image_id"
    )


    if not image_id:

        raise RuntimeError(
            "SerpApi did not return an image_id."
        )


    print(
        "Image uploaded successfully."
    )

    print(
        "Image ID received."
    )


    return image_id


# ============================================================
# SEARCH GOOGLE LENS THROUGH SERPAPI
# ============================================================

def search_google_lens(
    image_id
):

    print()
    print(
        "Searching Google Lens..."
    )


    parameters = {

        "engine":
            "google_lens",

        "image_id":
            image_id,

        "type":
            "all",

        "hl":
            "en",

        "country":
            "in",

        "safe":
            "active",

        "api_key":
            SERPAPI_API_KEY,

        "output":
            "json"
    }


    response = requests.get(

        SERPAPI_SEARCH_URL,

        params=parameters,

        timeout=90
    )


    try:

        data = response.json()

    except ValueError:

        raise RuntimeError(
            "SerpApi returned a non-JSON search response."
        )


    if response.status_code != 200:

        error_message = data.get(
            "error",
            f"HTTP {response.status_code}"
        )

        raise RuntimeError(
            f"Google Lens search failed: {error_message}"
        )


    if "error" in data:

        raise RuntimeError(
            f"Google Lens search failed: {data['error']}"
        )


    status = (
        data
        .get("search_metadata", {})
        .get("status")
    )


    print(
        "Search status:",
        status
    )


    return data


# ============================================================
# EXTRACT USEFUL RESULTS
# ============================================================

def extract_results(
    data
):

    exact_matches = []

    visual_matches = []

    related_content = []


    # --------------------------------------------------------
    # Exact/visual matches
    # --------------------------------------------------------

    for item in data.get(
        "exact_matches",
        []
    ):

        exact_matches.append({

            "title":
                item.get(
                    "title"
                ),

            "link":
                item.get(
                    "link"
                ),

            "source":
                item.get(
                    "source"
                ),

            "image":
                item.get(
                    "image"
                ),

            "thumbnail":
                item.get(
                    "thumbnail"
                ),

            "exact_match":
                True
        })


    # --------------------------------------------------------
    # Visual matches
    # --------------------------------------------------------

    for item in data.get(
        "visual_matches",
        []
    ):

        visual_matches.append({

            "title":
                item.get(
                    "title"
                ),

            "link":
                item.get(
                    "link"
                ),

            "source":
                item.get(
                    "source"
                ),

            "image":
                item.get(
                    "image"
                ),

            "thumbnail":
                item.get(
                    "thumbnail"
                ),

            "exact_match":
                bool(
                    item.get(
                        "exact_matches",
                        False
                    )
                )
        })


    # --------------------------------------------------------
    # Related content
    # --------------------------------------------------------

    for item in data.get(
        "related_content",
        []
    ):

        related_content.append({

            "query":
                item.get(
                    "query"
                ),

            "link":
                item.get(
                    "link"
                ),

            "thumbnail":
                item.get(
                    "thumbnail"
                )
        })


    return {

        "exact_matches":
            exact_matches,

        "visual_matches":
            visual_matches,

        "related_content":
            related_content
    }


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(
    results
):

    os.makedirs(
        os.path.dirname(
            RESULTS_FILE
        ),
        exist_ok=True
    )


    with open(
        RESULTS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            results,
            file,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# DISPLAY RESULTS
# ============================================================

def display_results(
    results
):

    exact_matches = results.get(
        "exact_matches",
        []
    )

    visual_matches = results.get(
        "visual_matches",
        []
    )

    related_content = results.get(
        "related_content",
        []
    )


    print()
    print(
        "========================================"
    )

    print(
        "        TRACEFACE WEB SEARCH"
    )

    print(
        "========================================"
    )


    print()
    print(
        "Exact matches:",
        len(exact_matches)
    )

    print(
        "Visual matches:",
        len(visual_matches)
    )

    print(
        "Related content:",
        len(related_content)
    )


    # --------------------------------------------------------
    # Exact matches
    # --------------------------------------------------------

    if exact_matches:

        print()
        print(
            "EXACT MATCHES"
        )

        print(
            "-------------"
        )


        for index, item in enumerate(
            exact_matches,
            start=1
        ):

            print()
            print(
                f"{index}.",
                item.get(
                    "title"
                )
            )

            print(
                "Source:",
                item.get(
                    "source"
                )
            )

            print(
                "URL:",
                item.get(
                    "link"
                )
            )

            print(
                "Image:",
                item.get(
                    "image"
                )
            )


    # --------------------------------------------------------
    # Visual matches
    # --------------------------------------------------------

    if visual_matches:

        print()
        print(
            "VISUAL MATCHES"
        )

        print(
            "--------------"
        )


        for index, item in enumerate(
            visual_matches,
            start=1
        ):

            print()
            print(
                f"{index}.",
                item.get(
                    "title"
                )
            )

            print(
                "Source:",
                item.get(
                    "source"
                )
            )

            print(
                "URL:",
                item.get(
                    "link"
                )
            )

            print(
                "Image:",
                item.get(
                    "image"
                )
            )


    # --------------------------------------------------------
    # Related content
    # --------------------------------------------------------

    if related_content:

        print()
        print(
            "RELATED CONTENT"
        )

        print(
            "---------------"
        )


        for index, item in enumerate(
            related_content,
            start=1
        ):

            print()
            print(
                f"{index}.",
                item.get(
                    "query"
                )
            )

            print(
                "URL:",
                item.get(
                    "link"
                )
            )


    print()
    print(
        "Results saved to:"
    )

    print(
        RESULTS_FILE
    )

    print()
    print(
        "========================================"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) != 2:

        print()
        print(
            "Usage:"
        )

        print(
            r'& "C:\Users\velis\.venv\Scripts\python.exe" web_search.py "PATH_TO_IMAGE"'
        )

        print()

        sys.exit(1)


    input_image = sys.argv[1]


    # --------------------------------------------------------
    # Prepare image
    # --------------------------------------------------------

    upload_path = None
    temporary_path = None


    try:

        upload_path, temporary_path = (
            prepare_image(
                input_image
            )
        )


        # ----------------------------------------------------
        # Upload
        # ----------------------------------------------------

        image_id = upload_image(
            upload_path
        )


        # ----------------------------------------------------
        # Lens search
        # ----------------------------------------------------

        raw_results = search_google_lens(
            image_id
        )


        # ----------------------------------------------------
        # Extract useful information
        # ----------------------------------------------------

        results = extract_results(
            raw_results
        )


        # Add metadata
        results["search_metadata"] = (
            raw_results.get(
                "search_metadata",
                {}
            )
        )


        results["search_parameters"] = (
            raw_results.get(
                "search_parameters",
                {}
            )
        )


        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        save_results(
            results
        )


        # ----------------------------------------------------
        # Display
        # ----------------------------------------------------

        display_results(
            results
        )


    except Exception as error:

        print()
        print(
            "ERROR:"
        )

        print(
            error
        )

        sys.exit(1)


    finally:

        # Delete temporary compressed image
        if temporary_path:

            try:

                os.remove(
                    temporary_path
                )

            except OSError:

                pass


if __name__ == "__main__":

    main()