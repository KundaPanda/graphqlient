class TestSimpleMutations:
    from generated.client_code import Client

    def test_mutation(self, client: Client):
        from generated.client_code import Job, PostJobInput, Company
        mutation = client.mutation.post_job(
            input_=PostJobInput(apply_url="https://www.example.com", commitment_id='123', description="description",
                                company_name='company', location_names='a,b,c', title='tester',
                                user_email='test@email.com')
        ).select(
            Job.slug,
            Job.title,
            Job.description,
            Job.company.select(
                Company.name,
            )
        )

        assert mutation.query
        assert not mutation.execute().get('errors')
