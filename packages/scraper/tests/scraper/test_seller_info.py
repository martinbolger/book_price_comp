from scraper.seller_info import EbaySellerInfo


def test_ebay_has_next_page():
    seller_info = EbaySellerInfo(seller_id="test_seller")
    # Mock HTML content with a next page link
    html_content = """
    <a href="https://www.ebay.com/sch/i.html?LH_Complete=1&amp;LH_Sold=1&amp;_fss=1&amp;_saslop=1&amp;_sasl=ninja_japan_shop&amp;LH_SpecificSeller=1&amp;_ipg=240&amp;_pgn=3" type="next" data-track="{&quot;eventFamily&quot;:&quot;LST&quot;,&quot;eventAction&quot;:&quot;ACTN&quot;,&quot;actionKind&quot;:&quot;NAVSRC&quot;,&quot;actionKinds&quot;:[&quot;NAVSRC&quot;],&quot;operationId&quot;:&quot;2351460&quot;,&quot;flushImmediately&quot;:false,&quot;eventProperty&quot;:{&quot;moduledtl&quot;:&quot;mi%3A4115%7Ciid%3A1%7Cli%3A1514%7Cluid%3Anext%7Ckind%3Apages%7C&quot;,&quot;pageci&quot;:&quot;7fb41757-411a-11f1-b4e1-2e4cc48d7ad1&quot;,&quot;parentrq&quot;:&quot;c7b0d93319d0a8971782c844fffbf012&quot;}}" _sp="p2351460.m4115.l8631" class="pagination__next icon-link" aria-label="Go to next search page" style="min-width:40px"><svg class="icon icon--16" focusable="false" aria-hidden="true"><use href="#icon-arrow-right-16"></use></svg></a>
    """
    assert seller_info.has_next_page(html_content) == True

    # Mock HTML content without a next page link
    html_content = """
    <button href="" type="next" class="pagination__next icon-btn" aria-disabled="true" aria-label="Go to next search page" style="min-width:40px"><svg class="icon icon--16" focusable="false" aria-hidden="true"><use href="#icon-arrow-right-16"></use></svg></button>
    """
    assert seller_info.has_next_page(html_content) == False
