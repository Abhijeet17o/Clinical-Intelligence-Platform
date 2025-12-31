"""Run an end-to-end timed transcription -> recommendation run and print timings.

Usage:
    python scripts/run_timed_e2e.py --audio path/to/file.wav --patient P1 --doctor D1
    OR
    python scripts/run_timed_e2e.py --transcript path/to/transcript.json

Outputs: prints timings and writes a copy of transcript (with _perf) to ./timed_output/
"""
import argparse
import os
import json
import logging

# Load .env from repo root if present so GEMINI_API_KEY is available
envpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(envpath):
    try:
        with open(envpath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())
    except Exception:
        pass

import sys
# Ensure project root is on sys.path so direct script execution can import modules
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from modules.transcription_engine import transcribe_conversation
from modules.recommendation_module import get_medicine_recommendations
from modules.utils.perf import get_records, clear_records

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('timed_e2e')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--audio', help='Path to audio file to transcribe')
    parser.add_argument('--transcript', help='Path to existing transcript JSON')
    parser.add_argument('--patient', default='TESTP')
    parser.add_argument('--doctor', default='TESTD')
    parser.add_argument('--top_n', type=int, default=5)
    args = parser.parse_args()

    os.makedirs('timed_output', exist_ok=True)

    transcript_path = None
    if args.audio:
        logger.info(f"Running transcription for {args.audio}")
        transcript_path = transcribe_conversation(args.audio, args.patient, args.doctor, output_dir='timed_output')
        logger.info(f"Transcript written to {transcript_path}")
    elif args.transcript:
        transcript_path = args.transcript
    else:
        logger.error('Either --audio or --transcript must be provided')
        return

    # Run recommendations
    logger.info('Running recommendations...')
    # Load a copy of medicines from DB or a small sample for timing
    try:
        from modules.database_module import MedicineDatabase
        db = MedicineDatabase('pharmacy.db')
        medicines = db.get_all_medicines()
        db.close_connection()
    except Exception:
        # small fallback
        medicines = [
            {'name': 'Paracetamol', 'description': 'pain relief and fever reducer', 'stock_level': 50, 'prescription_frequency': 1},
            {'name': 'Ibuprofen', 'description': 'anti-inflammatory', 'stock_level': 20, 'prescription_frequency': 1}
        ]

    recs = get_medicine_recommendations(transcript_path, medicines, top_n=args.top_n)
    logger.info(f"Recommendations: {recs}")

    # Print and persist perf records
    perf_list = get_records(reset=True)
    logger.info('=== TIMINGS ===')
    for name, sec in perf_list:
        logger.info(f"{name}: {sec:.3f}s")

    # Show transcription-level perf if present in the transcript JSON
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if '_perf' in data:
            logger.info('Transcription-level timings: ' + ', '.join(f"{k}={v:.3f}s" for k, v in data['_perf'].items()))
    except Exception:
        pass

    # Copy transcript to timed_output with perf added (if present)
    try:
        out_path = os.path.join('timed_output', os.path.basename(transcript_path))
        with open(transcript_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved instrumented transcript copy to {out_path}")
    except Exception as e:
        logger.warning(f"Could not copy transcript: {e}")


if __name__ == '__main__':
    main()
