from pathlib import Path

from gqlient.generator import generate

BASE_DIR = Path(__file__).parent

generate(BASE_DIR / "countries/schema.graphql", client_output=BASE_DIR / "countries/generated")

from countries.generated.client import *

client = Client(url="https://countries.trevorblades.com/")
result = client.query.countries(
    filter_=CountryFilterInput(code=StringQueryOperatorInput(eq="CZ"))
).select(
    Country.name,
    Country.currency,
    Country.states.select(State.name, State.country.select(Country.capital)),
    Country.continent.select(
        Continent.name,
        Continent.code,
        Continent.countries.select(Country.name)
    ),
)

print(result.query)
print(result.execute())

r2 = client.query.entities_(
    representations=[{"__typename": "Country", "code": "CZ"},
                     {"__typename": "Country", "code": "US"},
                     {"__typename": "Language", "code": "en"}]
).select(
    Entity_.on(Country).select(Country.name, Country.states.select(State.name)),
    Entity_.on(Continent).select(Continent.code),
    Entity_.on(Language).select(Language.native),
)

print(r2.query)
print(r2.execute())


r3 = client.query.continents(
    filter_=ContinentFilterInput(code=StringQueryOperatorInput(eq="EU"))
).select(
    Continent.name,
    Continent.countries.select(
        Country.name,
    )
).execute()

print(r3)
