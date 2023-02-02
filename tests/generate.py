from pathlib import Path

from gqlient.generator import generate

if __name__ == '__main__':
    BASE_DIR = Path(__file__).parent

    generate('http://localhost:8082/graphql/', BASE_DIR / 'netbox/generated')

    # generate(BASE_DIR / 'jobs/schema.graphql', client_output=BASE_DIR / 'jobs/generated')
    # generate(BASE_DIR / 'countries/schema.graphql', client_output=BASE_DIR / 'countries/generated')
