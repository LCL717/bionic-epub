from bionic_epub.tokenizer import bold_prefix, prefix_length


def test_prefix_lengths_follow_word_size_rules():
    assert prefix_length("the") == 3
    assert prefix_length("quick") == 2
    assert prefix_length("brown") == 2
    assert prefix_length("reading") == 3
    assert prefix_length("understand") == 4


def test_strength_changes_long_word_prefix():
    assert prefix_length("beautiful", "light") < prefix_length("beautiful", "standard")
    assert prefix_length("beautiful", "standard") < prefix_length("beautiful", "strong")


def test_urls_and_numbers_are_unchanged():
    assert bold_prefix("https://example.com") == ("https://example.com", 0)
    assert bold_prefix("12345") == ("12345", 0)
