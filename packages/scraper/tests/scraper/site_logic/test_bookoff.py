from scraper.site_logic.bookoff import BookOffStrategy

example_html = """
<div id="items_field" class="productItems js-toggleListTarget">
    <div class="productItems__inner">
        <div class="productItem js-hoverItem">
        <div class="productItem__inner">
            <a href="/used/0015580570" class="productItem__image js-hoverItemLink">
                <img src="https://content.bookoff.co.jp/goodsimages/LL/001558/0015580570LL.jpg" alt="砂の女 新潮文庫" class="js-gridImg -md" loading="lazy" />
            </a>
            <div class="productItem__detail">
                <a href="/used/0015580570" class="productItem__link js-hoverItemLink">
                <div class="productItem__tagList">
                <ul class="tagList">
                                                                                                                                    <li class="tag ">中古</li>
                                                <li class="tag tag--pickedUpStore">店舗受取可</li>
                                            </ul>
                </div>
                <ul class="productItem__genre">
                <li class="productItem__genreItem productItem__genreItem--category">
                    書籍
                </li>
                <li class="productItem__genreItem">文庫</li>
                </ul>
                <p class="productItem__title">砂の女 新潮文庫</p>
                <p class="productItem__author">安部公房</p>
                <p class="productItem__price">
            &yen;330<span class="productItem__moneyUnit">円</span><small>定価より451円（57%）おトク</small></p>
                <p class="productItem__point">獲得ポイント 3P</p>
                                                                            
                                                                                                                                                                <p class="productItem__stock"><span class="productItem__stock--alert">在庫あり</span></p>
                <p class="productItem__date">発売年月日：2003/03/01</p>
            </a>
            <div class="productItem__btns">
                        <div class="btn btn--orange jsBtn-cart ac-click-cv" data-cv-name="oldInCart_Search" data-mode="Add" data-item="0015580570" data-stock="used">
                        <span class="forPc btn__addTextWrap"><span class="btn__addText"> カートへ追加 </span></span>
                    <span class="forSp btn__addTextWrap"><span class="btn__addText"> カートへ追加 </span></span>
                    </div>
                <div class="productItem__favorite jsBtn-favorite ac-click-cv" data-cv-name="addBookmark_Search" data-mode="Add" data-item="0015580570">
                <span class="icon-favorite icon-favorite-on-dims js-favorite-star"></span>
                <span class="productItem__favoriteTxt">お気に入り追加</span>
                </div>

            </div>
            </div>
        </div>
        </div>
"""


def test_parse_extracts_expected_fields_from_example_html():
    strategy = BookOffStrategy(search_term="砂の女")

    records = strategy.parse(example_html)

    print(records)
    assert len(records) == 1
    record = records[0]
    assert record["raw_title"] == "砂の女 新潮文庫"
    assert record["raw_author"] == "安部公房"
    assert record["raw_price"] == "¥330円定価より451円（57%）おトク"
    assert record["raw_date"] == "発売年月日：2003/03/01"
    assert record["raw_rel_url"] == "/used/0015580570"
    assert record["raw_item_id"] == "0015580570"
