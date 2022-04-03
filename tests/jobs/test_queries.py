import pytest


@pytest.mark.usefixtures('generate_client')
class TestSimpleQueries:
    def test_query(self):
        from generated.client_code import Client, Job, Country, City, Tag

        client = Client('http://localhost:9002/graphql')
        query = client.query.jobs(
        ).select(
            Job.description,
            Job.created_at,
            Job.user_email,
            Job.countries.select(
                Country.name,
                Country.iso_code
            ),
            Job.cities.select(
                City.name,
                City.country.select(Country.created_at),
                City.id_,
                City.type_,
            ),
            Job.tags.select(
                Tag.name,
                Tag.jobs.select(
                    Job.is_featured
                )
            )
        )

        assert query.query
        assert not query.execute().get('errors')
