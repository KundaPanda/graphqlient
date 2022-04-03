class TestSimpleQueries:
    def test_query(self, client):
        from generated.client_code import City, Country, Job, Tag
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

    def test_interface(self, client):
        from generated.client_code import City, Country, CustomInterface
        query = client.query.interfaces(
        ).select(
            CustomInterface.name,
            CustomInterface.on(Country).select(
                Country.name,
                Country.cities.select(
                    City.name
                )
            )
        )

        assert query.query
        assert not query.execute().get('errors')

    def test_union(self, client):
        from generated.client_code import City, Country, CustomUnion
        query = client.query.unions(
        ).select(
            CustomUnion.on(Country).select(
                Country.name,
                Country.cities.select(
                    City.name
                )
            )
        )

        assert query.query
        assert not query.execute().get('errors')
