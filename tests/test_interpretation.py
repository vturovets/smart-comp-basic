from interpretation import interpret_results


def test_interpretation_local():
    class DummyConfig:
        def getboolean(self, section, option, fallback=False):
            return False  # simulate: no GPT API

        def get(self, section, option, fallback=None):
            return fallback

    dummy_results = {
        "003_comp_2_P95s": {
            "p95_1_empirical": 950.0,
            "p95_2_empirical": 1050.0,
            "p-value": 0.03,
            "alpha": 0.05,
            "significant difference": True,
            "p95_1_moe": 4.5,
            "p95_2_moe": 5.0
        }
    }

    interpretation = interpret_results(dummy_results, DummyConfig())
    print("\nGenerated interpretation:\n")
    print(interpretation)

    assert "statistically significant" in interpretation.lower()
    assert "p-value" in interpretation.lower()
    print("\n✅ Local fallback interpretation test passed.")

if __name__ == "__main__":
    test_interpretation_local()