import pytest
from ava_webhook.watcher import AvaWatcher


class TestCompanyNameVariants:
    """Unit tests for AvaWatcher._company_name_variants()"""

    @pytest.mark.parametrize(
        "input_name,expected_variants",
        [
            # Suffix stripping
            (
                "Bridgepoint Collective Inc.",
                ["bridgepoint collective"],
            ),
            (
                "Creative Artists Agency LLC",
                ["creative artists agency"],
            ),
            (
                "Amazon.com, Inc.",
                ["amazoncom inc"],
            ),
            # Trademark/copyright symbol removal
            (
                "LEGO®",
                ["lego"],
            ),
            (
                "Coca-Cola™",
                ["cocacola"],
            ),
            # HTML entity handling
            (
                "Ben & Jerry's",
                ["ben &amp; jerry's", "ben & jerrys"],
            ),
            # Punctuation differences
            (
                "e.l.f. Beauty",
                ["elf beauty"],
            ),
            # Multi-variant generation
            (
                "WME | William Morris Endeavor",
                ["wme william morris endeavor"],
            ),
            # No suffix — passes through
            (
                "The Gersh Agency",
                ["the gersh agency"],
            ),
            # Edge case: empty string
            ("", [""]),
        ],
    )
    def test_variants_contain_expected(self, input_name, expected_variants):
        variants = AvaWatcher._company_name_variants(input_name)
        for expected in expected_variants:
            assert expected in variants, (
                f"Expected variant '{expected}' not found in {variants}"
            )

    def test_empty_name_returns_single_empty_string(self):
        variants = AvaWatcher._company_name_variants("")
        assert variants == [""]

    def test_original_lowercase_always_present(self):
        variants = AvaWatcher._company_name_variants("Acme Corp.")
        assert "acme corp." in variants

    def test_stripped_version_present_for_suffixed_name(self):
        variants = AvaWatcher._company_name_variants("Acme Corporation")
        assert "acme" in variants

    def test_ampersand_variants_present(self):
        variants = AvaWatcher._company_name_variants("A&E Networks")
        assert "a&e networks" in variants
        assert "a&amp;e networks" in variants

    def test_trademark_symbols_removed(self):
        variants = AvaWatcher._company_name_variants("TechCorp® Inc.")
        assert "techcorp inc." in variants
        assert "techcorp" in variants

    def test_punctuation_stripped_variant(self):
        variants = AvaWatcher._company_name_variants("O'Reilly Media, Inc.")
        assert "oreilly media inc" in variants

    def test_no_duplicate_variants(self):
        variants = AvaWatcher._company_name_variants("Simple Co")
        assert len(variants) == len(set(variants))

    def test_suffix_with_comma(self):
        variants = AvaWatcher._company_name_variants("Widgets, Inc.")
        assert "widgets" in variants

    def test_co_suffix_stripped(self):
        variants = AvaWatcher._company_name_variants("Smith & Co.")
        assert "smith &" in variants

    def test_ltd_suffix_stripped(self):
        variants = AvaWatcher._company_name_variants("Global Holdings Ltd.")
        assert "global holdings" in variants

    def test_llc_suffix_stripped(self):
        variants = AvaWatcher._company_name_variants("StartUp LLC")
        assert "startup" in variants
