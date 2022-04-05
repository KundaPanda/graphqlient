from pathlib import Path

from generator import generate

BASE_DIR = Path(__file__).parent

generate(BASE_DIR / 'jobs/schema.graphql', client_output=BASE_DIR / 'jobs/generated')
generate(BASE_DIR / 'countries/schema.graphql', client_output=BASE_DIR / 'countries/generated')
