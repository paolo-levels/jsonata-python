import jsonata


class TestNullSafety:

    def test_null_safety(self):
        res = None
        res = jsonata.Jsonata("$sift(undefined, $uppercase)").evaluate(None)
        assert res is None

        res = jsonata.Jsonata("$each(undefined, $uppercase)").evaluate(None)
        assert res is None

        res = jsonata.Jsonata("$keys(undefined)").evaluate(None)
        assert res is None

        res = jsonata.Jsonata("$map(undefined, $uppercase)").evaluate(None)
        assert res is None

        res = jsonata.Jsonata("$filter(undefined, $uppercase)").evaluate(None)
        assert res is None

        res = jsonata.Jsonata("$single(undefined, $uppercase)").evaluate(None)
        assert res is None

        res = jsonata.Jsonata("$reduce(undefined, $uppercase)").evaluate(None)
        assert res is None

        res = jsonata.Jsonata("$lookup(undefined, 'anykey')").evaluate(None)
        assert res is None

        res = jsonata.Jsonata("$spread(undefined)").evaluate(None)
        assert res is None
