from flask import Flask, render_template, request
import cv2
import os
import json
import tempfile
import requests

from werkzeug.utils import secure_filename

from evidence import create_evidence

from blockchain.blockchain import (
    record_hash_on_chain,
    wait_for_confirmation,
    verify_hash
)

from web_search import (
    prepare_image,
    upload_image,
    search_google_lens,
    extract_results
)


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# ============================================================
# PROJECT PATHS
# ============================================================

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

WEB_RESULTS_FILE = os.path.join(
    BASE_DIR,
    "data",
    "web_results.json"
)

EVIDENCE_FILE = os.path.join(
    BASE_DIR,
    "data",
    "evidence_records.json"
)


os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    os.path.join(
        BASE_DIR,
        "data"
    ),
    exist_ok=True
)


# ============================================================
# AI MODEL PATHS
# ============================================================

DETECTOR_MODEL = os.path.join(
    BASE_DIR,
    "models",
    "face_detection_yunet.onnx"
)

RECOGNIZER_MODEL = os.path.join(
    BASE_DIR,
    "models",
    "face_recognition_sface.onnx"
)


# ============================================================
# LOAD YUNET
# ============================================================

detector = cv2.FaceDetectorYN.create(
    DETECTOR_MODEL,
    "",
    (320, 320),
    0.9,
    0.3,
    5000
)


# ============================================================
# LOAD SFACE
# ============================================================

recognizer = cv2.FaceRecognizerSF.create(
    RECOGNIZER_MODEL,
    ""
)


# ============================================================
# DETECT ALL FACES IN IMAGE
# ============================================================

def detect_faces(
    image
):

    if image is None:
        return []

    height, width = image.shape[:2]

    detector.setInputSize(
        (width, height)
    )

    _, faces = detector.detect(
        image
    )

    if faces is None:
        return []

    return list(faces)


# ============================================================
# CREATE FEATURE FROM A FACE
# ============================================================

def create_face_feature(
    image,
    face
):

    try:

        aligned_face = recognizer.alignCrop(
            image,
            face
        )

        feature = recognizer.feature(
            aligned_face
        )

        return feature

    except Exception:

        return None


# ============================================================
# CREATE QUERY FEATURE
# ============================================================

def create_query_feature(
    image
):

    faces = detect_faces(
        image
    )

    if not faces:

        return None, "No face detected."

    # Select the largest face
    query_face = max(
        faces,
        key=lambda face:
            float(face[2]) * float(face[3])
    )

    feature = create_face_feature(
        image,
        query_face
    )

    if feature is None:

        return None, (
            "Could not create face feature."
        )

    return feature, None


# ============================================================
# COMPARE QUERY AGAINST ALL FACES IN CANDIDATE IMAGE
# ============================================================

def compare_query_with_image(
    query_feature,
    candidate_image
):

    faces = detect_faces(
        candidate_image
    )

    if not faces:

        return None

    best_score = None

    for face in faces:

        candidate_feature = (
            create_face_feature(
                candidate_image,
                face
            )
        )

        if candidate_feature is None:
            continue

        score = recognizer.match(
            query_feature,
            candidate_feature,
            cv2.FaceRecognizerSF_FR_COSINE
        )

        score = float(
            score
        )

        if (
            best_score is None
            or score > best_score
        ):

            best_score = score

    return best_score


# ============================================================
# DOWNLOAD WEB IMAGE
# ============================================================

def download_web_image(
    image_url
):

    if not image_url:

        return None

    try:

        response = requests.get(
            image_url,
            timeout=20,
            headers={
                "User-Agent":
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/140 Safari/537.36"
            },
            stream=True
        )

        if response.status_code != 200:

            return None


        content_type = (
            response.headers
            .get(
                "Content-Type",
                ""
            )
            .lower()
        )


        # Accept normal image responses
        # but don't reject if server omitted
        # a Content-Type header.
        if (
            content_type
            and "image" not in content_type
        ):

            return None


        content = bytearray()

        max_download_size = (
            8 * 1024 * 1024
        )


        for chunk in response.iter_content(
            chunk_size=65536
        ):

            if not chunk:
                continue

            content.extend(
                chunk
            )

            if len(content) > (
                max_download_size
            ):

                return None


        if not content:

            return None


        array = __import__(
            "numpy"
        ).frombuffer(
            bytes(content),
            dtype=__import__(
                "numpy"
            ).uint8
        )


        image = cv2.imdecode(
            array,
            cv2.IMREAD_COLOR
        )


        if image is None:

            return None


        return image

    except Exception:

        return None


# ============================================================
# SEARCH THE WEB
# ============================================================

def perform_web_search(
    uploaded_image_path
):

    temporary_path = None

    try:

        # ----------------------------------------------------
        # Prepare image for SerpApi
        # ----------------------------------------------------

        upload_path, temporary_path = (
            prepare_image(
                uploaded_image_path
            )
        )


        # ----------------------------------------------------
        # Upload image
        # ----------------------------------------------------

        image_id = upload_image(
            upload_path
        )


        # ----------------------------------------------------
        # Google Lens
        # ----------------------------------------------------

        raw_results = (
            search_google_lens(
                image_id
            )
        )


        # ----------------------------------------------------
        # Extract useful results
        # ----------------------------------------------------

        extracted = extract_results(
            raw_results
        )


        # Save complete web-search result
        web_data = {

            "exact_matches":
                extracted[
                    "exact_matches"
                ],

            "visual_matches":
                extracted[
                    "visual_matches"
                ],

            "related_content":
                extracted[
                    "related_content"
                ],

            "search_metadata":
                raw_results.get(
                    "search_metadata",
                    {}
                )
        }


        with open(
            WEB_RESULTS_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                web_data,
                file,
                indent=4,
                ensure_ascii=False
            )


        return extracted

    finally:

        if temporary_path:

            try:

                os.remove(
                    temporary_path
                )

            except OSError:

                pass


# ============================================================
# FIND FACE MATCHES AMONG WEB RESULTS
# ============================================================

def find_web_face_matches(
    query_feature,
    web_results,
    max_results=20
):

    candidates = []

    seen_urls = set()


    # --------------------------------------------------------
    # Exact matches first
    # --------------------------------------------------------

    ordered_results = []

    ordered_results.extend(
        web_results.get(
            "exact_matches",
            []
        )
    )

    ordered_results.extend(
        web_results.get(
            "visual_matches",
            []
        )
    )


    # --------------------------------------------------------
    # Limit number of downloaded images
    # --------------------------------------------------------

    for item in ordered_results:

        if len(candidates) >= max_results:
            break


        page_url = item.get(
            "link"
        )

        image_url = item.get(
            "image"
        )


        if not page_url:

            continue


        if page_url in seen_urls:

            continue


        seen_urls.add(
            page_url
        )


        if not image_url:

            continue


        # ----------------------------------------------------
        # Download image from web result
        # ----------------------------------------------------

        candidate_image = (
            download_web_image(
                image_url
            )
        )


        if candidate_image is None:

            continue


        # ----------------------------------------------------
        # Face comparison
        # ----------------------------------------------------

        similarity = (
            compare_query_with_image(
                query_feature,
                candidate_image
            )
        )


        if similarity is None:

            continue


        candidates.append({

            "id":
                f"WEB-{len(candidates) + 1:03d}",

            "title":
                item.get(
                    "title",
                    "Public Web Result"
                ),

            "source":
                item.get(
                    "source",
                    "Web"
                ),

            "url":
                page_url,

            "image":
                image_url,

            "similarity":
                similarity,

            "exact_match":
                bool(
                    item.get(
                        "exact_match",
                        False
                    )
                )
        })


    # --------------------------------------------------------
    # Highest face similarity first
    # --------------------------------------------------------

    candidates.sort(
        key=lambda item:
            item["similarity"],
        reverse=True
    )


    return candidates


# ============================================================
# UPDATE EVIDENCE BLOCKCHAIN DATA
# ============================================================

def update_evidence_blockchain(
    evidence_id,
    blockchain_data
):

    if not os.path.exists(
        EVIDENCE_FILE
    ):

        return


    try:

        with open(
            EVIDENCE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            records = json.load(
                file
            )

    except (
        json.JSONDecodeError,
        OSError
    ):

        return


    for record in records:

        evidence = record.get(
            "evidence",
            {}
        )


        if (
            evidence.get(
                "evidence_id"
            )
            == evidence_id
        ):

            record[
                "blockchain"
            ] = blockchain_data

            break


    try:

        with open(
            EVIDENCE_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                records,
                file,
                indent=4,
                ensure_ascii=False
            )

    except OSError:

        pass


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# ============================================================
# ANALYZE
# ============================================================

@app.route(
    "/analyze",
    methods=["POST"]
)
def analyze():

    # --------------------------------------------------------
    # Check upload
    # --------------------------------------------------------

    if "photo" not in request.files:

        return render_template(
            "result.html",
            success=False,
            message="No photo uploaded."
        )


    uploaded_file = request.files[
        "photo"
    ]


    if uploaded_file.filename == "":

        return render_template(
            "result.html",
            success=False,
            message="No file selected."
        )


    filename = secure_filename(
        uploaded_file.filename
    )


    if not filename:

        return render_template(
            "result.html",
            success=False,
            message="Invalid filename."
        )


    # --------------------------------------------------------
    # Save upload
    # --------------------------------------------------------

    uploaded_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )


    try:

        uploaded_file.save(
            uploaded_path
        )

    except OSError:

        return render_template(
            "result.html",
            success=False,
            message="Could not save uploaded image."
        )


    # --------------------------------------------------------
    # Read upload
    # --------------------------------------------------------

    query_image = cv2.imread(
        uploaded_path
    )


    if query_image is None:

        return render_template(
            "result.html",
            success=False,
            message="Could not read uploaded image."
        )


    # --------------------------------------------------------
    # Detect + encode uploaded face
    # --------------------------------------------------------

    query_feature, error = (
        create_query_feature(
            query_image
        )
    )


    if error:

        return render_template(
            "result.html",
            success=False,
            message=error
        )


    # ========================================================
    # WEB SEARCH
    # ========================================================

    try:

        web_results = (
            perform_web_search(
                uploaded_path
            )
        )

    except Exception as error:

        return render_template(

            "result.html",

            success=False,

            message=(
                "Face detection succeeded, "
                "but web search failed: "
                f"{error}"
            )
        )


    total_web_results = (
        len(
            web_results.get(
                "exact_matches",
                []
            )
        )
        +
        len(
            web_results.get(
                "visual_matches",
                []
            )
        )
    )


    # ========================================================
    # FACE MATCH WEB RESULTS
    # ========================================================

    web_matches = (
        find_web_face_matches(
            query_feature,
            web_results,
            max_results=20
        )
    )


    # --------------------------------------------------------
    # No usable web face matches
    # --------------------------------------------------------

    if not web_matches:

        return render_template(

            "result.html",

            success=False,

            message=(
                f"Google Lens found "
                f"{total_web_results} web image results, "
                "but no returned image could be "
                "successfully processed for a face match."
            ),

            web_results_count=
                total_web_results
        )


    # ========================================================
    # SELECT BEST WEB FACE MATCH
    # ========================================================

    best_match = web_matches[0]


    # ========================================================
    # FACE MATCH THRESHOLD
    # ========================================================

    MATCH_THRESHOLD = 0.363


    match_found = (
        best_match["similarity"]
        >= MATCH_THRESHOLD
    )


    # ========================================================
    # EVIDENCE + BLOCKCHAIN
    # ========================================================

    evidence_record = None

    blockchain_status = (
        "NOT_RECORDED"
    )

    transaction_hash = None

    blockchain_verification = None


    if match_found:

        # ----------------------------------------------------
        # Create evidence
        # ----------------------------------------------------

        try:

            evidence_record = (
                create_evidence(
                    best_match,
                    filename
                )
            )

        except Exception as error:

            return render_template(

                "result.html",

                success=False,

                message=(
                    "Web face match succeeded, "
                    "but evidence creation failed: "
                    f"{error}"
                )
            )


        sha256_hash = (
            evidence_record[
                "sha256"
            ]
        )


        evidence_id = (
            evidence_record[
                "evidence"
            ][
                "evidence_id"
            ]
        )


        # ----------------------------------------------------
        # Blockchain submission
        # ----------------------------------------------------

        try:

            blockchain_status = (
                "SUBMITTING"
            )


            update_evidence_blockchain(

                evidence_id,

                {
                    "status":
                        blockchain_status,

                    "transaction_hash":
                        None
                }
            )


            # Send SHA-256 on-chain
            transaction_hash = (
                record_hash_on_chain(
                    sha256_hash
                )
            )


            blockchain_status = (
                "CONFIRMING"
            )


            update_evidence_blockchain(

                evidence_id,

                {
                    "status":
                        blockchain_status,

                    "transaction_hash":
                        transaction_hash
                }
            )


            # ------------------------------------------------
            # Wait for confirmation
            # ------------------------------------------------

            receipt = (
                wait_for_confirmation(
                    transaction_hash
                )
            )


            if int(
                receipt["status"]
            ) != 1:

                blockchain_status = (
                    "FAILED"
                )

                final_data = {

                    "status":
                        blockchain_status,

                    "transaction_hash":
                        transaction_hash,

                    "block_number":
                        receipt[
                            "blockNumber"
                        ]
                }

                update_evidence_blockchain(

                    evidence_id,

                    final_data
                )


                evidence_record[
                    "blockchain"
                ] = final_data


            else:

                # --------------------------------------------
                # Read and verify on-chain
                # --------------------------------------------

                blockchain_verification = (
                    verify_hash(
                        transaction_hash,
                        sha256_hash
                    )
                )


                if blockchain_verification[
                    "valid"
                ]:

                    blockchain_status = (
                        "CONFIRMED"
                    )

                else:

                    blockchain_status = (
                        "VERIFICATION_FAILED"
                    )


                final_data = {

                    "status":
                        blockchain_status,

                    "transaction_hash":
                        transaction_hash,

                    "block_number":
                        receipt[
                            "blockNumber"
                        ],

                    "on_chain_sha256":
                        blockchain_verification[
                            "blockchain_hash"
                        ],

                    "verified":
                        blockchain_verification[
                            "valid"
                        ]
                }


                update_evidence_blockchain(

                    evidence_id,

                    final_data
                )


                evidence_record[
                    "blockchain"
                ] = final_data


        except Exception as error:

            blockchain_status = (
                "FAILED"
            )


            error_data = {

                "status":
                    blockchain_status,

                "transaction_hash":
                    transaction_hash,

                "error":
                    str(error)
            }


            update_evidence_blockchain(

                evidence_id,

                error_data
            )


            evidence_record[
                "blockchain"
            ] = error_data


    # ========================================================
    # DISPLAY
    # ========================================================

    return render_template(

        "result.html",

        success=True,

        match_found=match_found,

        best_match=best_match,

        matches=web_matches,

        evidence_record=evidence_record,

        blockchain_status=
            blockchain_status,

        transaction_hash=
            transaction_hash,

        blockchain_verification=
            blockchain_verification,

        web_results_count=
            total_web_results,

        message=(
            "Face detected, public web content "
            "searched, and returned images "
            "were compared using SFace."
        )
    )


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )