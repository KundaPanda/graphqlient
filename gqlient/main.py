from generated.client_code import *

client = Client(url="https://countries.trevorblades.com/")
result = client.query\
    .countries(filter_=CountryFilterInput(code=StringQueryOperatorInput(eq='CZ')))\
    .select(Country.name,
            Country.currency,
            Country.states.select(
                State.name, State.country.select(
                    Country.capital
                )
            ),
            Country.currency,
            Country.continent.select(
                Continent.name, Continent.code, Continent.countries.select(
                    Country.name
                )
            ))

print(result.query)
print(result.execute())
