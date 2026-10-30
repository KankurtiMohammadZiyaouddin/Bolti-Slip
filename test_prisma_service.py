"""
test_prisma_service.py
----------------------
Smoke test for the reusable PrismaService.

Calls the service with test_audio.wav and displays the actual
structured response returned by the Gnani AI Prisma v3.0 API.

Usage:
    ./.venv/Scripts/Activate.ps1   # activate virtual environment
    python test_prisma_service.py
"""

from pathlib import Path

from services.prisma import PrismaService

AUDIO_FILE = Path(__file__).parent / "test_audio.wav"


def main() -> None:
    print("=" * 60)
    print("  PrismaService — smoke test")
    print("=" * 60)

    # Instantiate — raises EnvironmentError if GNANI_API_KEY_ID is missing.
    try:
        svc = PrismaService()
    except EnvironmentError as exc:
        print(f"[ERROR] {exc}")
        return

    print(f"  Endpoint      : {svc.endpoint}")
    print(f"  Model         : {svc.model}")
    print(f"  Language code : {svc.language_code}")
    print(f"  Format        : {svc.format}")
    print(f"  Audio file    : {AUDIO_FILE.name}")
    print("-" * 60)

    result = svc.transcribe(AUDIO_FILE)

    if result["success"]:
        print(f"  success                  : {result['success']}")
        print(f"  transcript               : {result['transcript']}")
        print(f"  language                 : {result['detected_language_code'] or 'N/A'}")
        print(f"  model                    : {result['model']}")
        print(f"  http_status_code         : {result['http_status_code']}")
        print(f"  request_elapsed_seconds  : {result['request_elapsed_seconds']}s")
        print(f"  api_processing_time      : {result['api_processing_time'] or 'N/A'}")
        print(f"  request_id               : {result['request_id'] or 'N/A'}")

        extras = {
            k: v for k, v in (result["raw_response"] or {}).items()
            if k not in {
                "transcript", "text", "result",
                "detected_language_code", "language_code",
                "request_id", "requestId", "id",
                "processing_time", "processingTime", "duration_ms", "duration",
            }
        }
        if extras:
            print("\n  Other API response fields:")
            for k, v in extras.items():
                print(f"    {k}: {v}")
    else:
        print(f"  success                  : {result['success']}")
        print(f"  error_type               : {result['error_type']}")
        print(f"  error                    : {result['error']}")
        if result["request_elapsed_seconds"] is not None:
            print(f"  request_elapsed_seconds  : {result['request_elapsed_seconds']}s")

    print("=" * 60)


if __name__ == "__main__":
    main()
