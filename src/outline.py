from playwright.sync_api import sync_playwright, ProxySettings, expect
import time, datetime
import json
from urllib.parse import unquote
import os

# target_url = 'https://www.amazon.co.jp/s?k=iphone%E3%82%B1%E3%83%BC%E3%82%B9&__mk_ja_JP=%E3%82%AB%E3%82%BF%E3%82%AB%E3%83%8A&crid=WZP8S0OOZKXK&sprefix=iphone%E3%82%B1%E3%83%BC%E3%82%B9%2Caps%2C171&ref=nb_sb_noss_1'
amazon_url = "https://www.amazon.co.jp"
amazon_url = "https://www.amazon.com"


def run(search_keyword):
    # search_keyword = "mahjong"

    dev_writefile_flag = True
    next_page_flag = True
    max_page = 21
    out = {}
    sponsored_labels = {"jp": "スポンサー", "us": "Sponsored"}
    prime_lables = {"jp": "Amazon プライム", "us": "Prime"}
    locale = "us"

    def fully_decode(str_uri):
        prev_uri = ""
        while str_uri != prev_uri:
            prev_uri = str_uri
            str_uri = unquote(str_uri)
        return str_uri

    dt_now = datetime.datetime.now()
    start_time = time.time()

    context_proxy = ProxySettings(
        server="socks5://127.0.0.1:1080"
        # username=username,
        # password=password,
    )
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        # browser = p.chromium.launch(proxy=context_proxy)
        page = browser.new_page()
        page.goto(amazon_url)
        page.wait_for_load_state()
        page.fill("input#twotabsearchtextbox", search_keyword)
        page.press("input#twotabsearchtextbox", "Enter")
        page.wait_for_load_state()
        target_url = page.url
        print(f"current_url: {target_url}")
        out["keyWord"] = search_keyword
        out["startDate"] = dt_now.strftime("%Y %m %d %H:%M:%S")
        out["targetUrls"] = []
        out["Cards"] = []
        loop_num = 0
        while next_page_flag:
            out["targetUrls"].append(target_url)
            page.goto(target_url)
            # page.press('body', 'End')
            page.keyboard.press("PageDown")
            time.sleep(3)
            page.wait_for_load_state()
            hit_count_element = (
                page.locator(".a-section.a-spacing-small.a-spacing-top-small")
                .all()[0]
                .inner_text()
            )
            print(hit_count_element)
            Cards = page.locator(".a-section.a-spacing-base").all()
            for index, card in enumerate(Cards):
                loop_num += 1
                indexPlus1 = index + 1
                idd = f'{str(loop_num)}_{len(out["targetUrls"])}_{str(indexPlus1)}'
                # print(indexPlus1)
                temp_card = {
                    "id": idd,
                    "imageUrl": "",
                    "sponsored": False,
                    "title": "",
                    "stars": "",
                    "ratingsCount": "",
                    "salesText": "",
                    "lastmonthsales": "",
                    "price": "",
                    "prePrice": "",
                    "couponText": "",
                    "prime": False,
                    "primeicon": False,
                    "url": "",
                }
                # imageUrl
                image_element = card.locator("img.s-image").all()
                if len(image_element) > 0:
                    temp_card["imageUrl"] = image_element[-1].get_attribute("src")
                # sponsored
                # 1) <span class="puis-label-popover-default">…</span> aka locator(".puis-label-popover").first
                # 2) <span class="puis-label-popover-hover">…</span> aka locator(".puis-label-popover").first
                # 3) <span class="aok-inline-block puis-sponsored-label-inf…></span> aka locator(".puis-label-popover").first
                if card.locator(
                    ".puis-label-popover-default > .a-color-secondary"
                ).is_visible():
                    for i in len(
                        card.locator(".puis-sponsored-label-text > span").all()
                    ):
                        print(card.locator(".puis-label-popover")[i].inner_text())

                    sponsored_element = card.locator(
                        ".puis-label-popover-default > .a-color-secondary"
                    )
                    sponsored_text = sponsored_element.inner_text()
                    if sponsored_text == sponsored_labels[locale]:

                        temp_card["sponsored"] = True

                # title
                title_element = card.locator(
                    ".a-size-base-plus.a-color-base.a-text-normal"
                )
                if title_element:
                    title = title_element.inner_text()
                    temp_card["title"] = title
                # stars
                # ratingsCount
                # 2.8K+となる場合、￥1,450\n￥1,450価格になる場合があるので、属性の値を取得する
                aria_label_elements = card.locator(".a-row.a-size-small > span").all()
                if aria_label_elements:
                    print(f"found {len(aria_label_elements)}")
                    t = 0
                    for i in aria_label_elements:
                        print(f" {t}text:", i.inner_text())
                        t = t + 1

                    stars_text = aria_label_elements[0].get_attribute("aria-label")
                    temp_card["stars"] = stars_text
                    if stars_text and "out of 5 stars" in stars_text:

                        temp_card["stars"] = stars_text.replace(" out of 5 stars", "")

                    if len(aria_label_elements) > 2:
                        # print(" html:", aria_label_elements[1].inner_html())

                        temp_card["ratingsCount"] = (
                            aria_label_elements[1]
                            .locator("div>span")
                            .get_attribute("aria-label")
                        )
                        if (
                            temp_card["ratingsCount"]
                            and "ratings" in temp_card["ratingsCount"]
                        ):

                            temp_card["ratingsCount"].replace(" ratings", "")
                else:
                    print("評価なし")

                # sales
                if card.locator(
                    '[data-a-badge-color="sx-lightning-deal-red"].a-badge-label > .a-badge-label-inner.a-text-ellipsis'
                ).is_visible():
                    sales_element = card.locator(
                        '[data-a-badge-color="sx-lightning-deal-red"].a-badge-label > .a-badge-label-inner.a-text-ellipsis'
                    )
                    sales_text = sales_element.inner_text()
                    temp_card["salesText"] = sales_text
                # lastmonthsales
                if card.locator(
                    "div:nth-child(2) > div:nth-child(2) > div:nth-child(2) > .a-size-base"
                ).first.is_visible():

                    lastmonthsales_element = card.locator(
                        "div:nth-child(2) > div:nth-child(2) > div:nth-child(2) > .a-size-base"
                    ).first

                    lastmonthsales_text = lastmonthsales_element.inner_text()
                    if (
                        lastmonthsales_text
                        and "bought in past month" in lastmonthsales_text
                    ):
                        lastmonthsales_text = lastmonthsales_text.replace(
                            "+ bought in past month", ""
                        )
                    temp_card["lastmonthsales"] = lastmonthsales_text

                # price
                if card.locator(".a-price-whole").is_visible():

                    price_element = card.locator(".a-price-whole")
                    price_text = price_element.inner_text()
                    temp_card["price"] = price_text
                # pre_price
                if card.locator(
                    '.a-price.a-text-price[data-a-strike="true"] > .a-offscreen'
                ).is_visible():
                    pre_price_element = card.locator(
                        '.a-price.a-text-price[data-a-strike="true"] > .a-offscreen'
                    )
                    pre_price_text = pre_price_element.inner_text()
                    temp_card["prePrice"] = pre_price_text
                # coupon
                if card.locator(".s-coupon-unclipped").is_visible():
                    coupon_element = card.locator(".s-coupon-unclipped")
                    coupon_text = coupon_element.inner_text()
                    temp_card["couponText"] = coupon_text
                # prime
                if card.locator(
                    f'[role="img"][aria-label="{prime_lables[locale]}"]'
                ).is_visible():

                    prime_element = card.locator(
                        f'[role="img"][aria-label="{prime_lables[locale]}"]'
                    )
                    temp_card["prime"] = True

                if card.locator(".a-icon.a-icon-prime.a-icon-medium").is_visible():
                    prime_element = card.locator(".a-icon.a-icon-prime.a-icon-medium")
                    prime_text = prime_element.get_attribute("aria-label")
                    if prime_text == prime_lables[locale]:
                        temp_card["primeicon"] = True

                # url

                if card.locator(
                    "a.a-link-normal.s-underline-text.s-underline-link-text.s-link-style.a-text-normal"
                ):

                    url_element = card.locator(
                        "a.a-link-normal.s-underline-text.s-underline-link-text.s-link-style.a-text-normal"
                    ).all()[0]
                    url_txt = url_element.get_attribute("href")
                    if url_txt:
                        if "url=" in url_txt:
                            split_str = url_txt.split("url=")[1]
                        else:
                            split_str = url_txt
                        decoded_string = fully_decode(split_str)
                        temp_card["url"] = amazon_url + decoded_string

                out["Cards"].append(temp_card)
            print(f"listing counts: {len(Cards)}")

            # ページネーション
            pagination_element = page.locator("span.s-pagination-strip")
            # 現在のページ
            current_page_element = pagination_element.locator(".s-pagination-selected")
            current_page = current_page_element.inner_text()
            print(f"current_page_number: {current_page}")
            # 次ページ
            next_page_element = pagination_element.locator(
                ".s-pagination-item.s-pagination-next"
            )
            print(next_page_element.inner_html())
            if next_page_element.get_attribute("href"):
                target_url = amazon_url + next_page_element.get_attribute("href")
                next_page_flag = True
            else:
                target_url = ""
                next_page_flag = False
            print(f"nextPage: {target_url}")
            if dev_writefile_flag:
                html_content = page.content()
                print(len(html_content))
                with open(
                    search_keyword + "_output.html", "w", encoding="utf8"
                ) as file:
                    file.write(html_content)
            if int(current_page) >= max_page:
                next_page_flag = False
                print(f"max_page:{max_page} process finished。")
                break
        browser.close()
    # with open(search_keyword + "cards.json", "w", encoding="utf-8") as file:
    #     json.dump(out, file, ensure_ascii=False, indent=4)
    processing_time = time.time() - start_time
    print(f"processing time(s）: {round(processing_time,1)}")

    return json.dumps(out, file, ensure_ascii=False, indent=4)


# with open("k-list.txt", "r") as r:
#     keywords = [p.strip() for p in r.readlines()]
#     for k in keywords:
#         if k and os.path.exists(k + "cards.json") == False:
#             print(f"start to process {k}")
#             run(k)
