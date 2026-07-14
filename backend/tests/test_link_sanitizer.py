from app.services.nodes.utils import sanitize_reply_links


CONTEXT = """
Rules with sources:
- Official source: [B.Sc. SPO 2023](https://www.fu-berlin.de/service/zuvdocs/amtsblatt/2023/ab232023.pdf)
- Step 1: [Moses](https://moseskonto.tu-berlin.de/moses/verzeichnis/veranstaltungen/vkpl_stg.html)
- Contact: Prof. Dr. Claudia Müller-Birn (clmb@inf.fu-berlin.de)
"""


def test_exact_url_is_kept():
    reply = "See [SPO](https://www.fu-berlin.de/service/zuvdocs/amtsblatt/2023/ab232023.pdf)."
    assert sanitize_reply_links(reply, CONTEXT) == reply


def test_mangled_url_is_repaired_to_context_url():
    reply = "See [SPO](https://www.fu-berlin.de/service/zuvdocs/amsblatt/23/ab232023.pdf)."
    assert (
        sanitize_reply_links(reply, CONTEXT)
        == "See [SPO](https://www.fu-berlin.de/service/zuvdocs/amtsblatt/2023/ab232023.pdf)."
    )


def test_invented_markdown_link_is_reduced_to_label():
    reply = "Details in den [Ordnungen](https://www.mi.fu-berlin.de/studium/ordnungen/)."
    assert sanitize_reply_links(reply, CONTEXT) == "Details in den Ordnungen."


def test_anchor_link_is_reduced_to_label():
    reply = "See the [Bachelorarbeit section](#BACHELORARBEIT)."
    assert sanitize_reply_links(reply, CONTEXT) == "See the Bachelorarbeit section."


def test_invented_bare_url_is_removed():
    reply = "Mehr unter https://www.example.com/erfunden."
    assert sanitize_reply_links(reply, CONTEXT) == "Mehr unter ."


def test_known_bare_url_is_kept_with_trailing_punctuation():
    reply = "Moses: https://moseskonto.tu-berlin.de/moses/verzeichnis/veranstaltungen/vkpl_stg.html."
    assert sanitize_reply_links(reply, CONTEXT) == reply


def test_known_mailto_is_kept_and_unknown_is_stripped():
    reply = "Write to [clmb@inf.fu-berlin.de](mailto:clmb@inf.fu-berlin.de) or [someone](mailto:fake@example.com)."
    assert (
        sanitize_reply_links(reply, CONTEXT)
        == "Write to [clmb@inf.fu-berlin.de](mailto:clmb@inf.fu-berlin.de) or someone."
    )


def test_plain_text_is_untouched():
    reply = "Die Bachelorarbeit umfasst 12 LP (RSPO §7)."
    assert sanitize_reply_links(reply, CONTEXT) == reply
