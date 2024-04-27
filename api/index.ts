import { NextApiRequest, NextApiResponse } from "next"
const { chromium: playwright } = require('playwright-core')
const sparticuzChromium = require("@sparticuz/chromium-min")
import * as fs from 'fs'
import * as path from 'path'
import { unquote } from 'querystring'

const amazonUrl = 'https://www.amazon.co.jp'
// const amazonUrl = 'https://www.amazon.com';
const formatKeywords = (keywords: string) => {
  return keywords.replace(/\s+/g, '%20')
}
interface Card {
  id: string
  imageUrl: string
  sponsored: boolean
  title: string
  stars: string
  ratingsCount: string
  salesText: string
  lastmonthsales: string
  price: string
  prePrice: string
  couponText: string
  prime: boolean
  primeicon: boolean
  url: string
}

interface Output {
  keyWord: string
  startDate: string
  targetUrls: string[]
  Cards: Card[]
}

const run = async (searchKeyword: string): Promise<string> => {
  const devWritefileFlag = true
  let nextPageFlag = true
  const maxPage = 21
  const out: Output = {
    keyWord: searchKeyword,
    startDate: new Date().toLocaleString(),
    targetUrls: [],
    Cards: [],
  }

  const sponsoredLabels = { jp: 'スポンサー', us: 'Sponsored' }
  const primeLables = { jp: 'Amazon プライム', us: 'Prime' }
  const locale = 'us'

  const fullyDecode = (strUri: string): string => {
    let prevUri = ''
    while (strUri !== prevUri) {
      prevUri = strUri
      strUri = unquote(strUri)
    }
    return strUri
  }

  const startTime = Date.now()
  sparticuzChromium.setHeadlessMode = true
  export default async function handler(
    request: NextApiRequest,
    response: NextApiResponse
  ) {

    const { url, query, method } = request
    const id = parseInt(query.id as string, 10)
    const name = query.name as string

    switch (method) {
      case "GET":

        if (request.url.includes('/api/amz')) {

          let inputKeywords = request.url?.replace("/api/amz", "")

          if (!inputKeywords) {
            response.status(400).send("Missing inputKeywords parameter")
            return
          }

          // Example usage
          // const inputKeywords = "sectional sofa"
          let formattedKeywords
          if (inputKeywords.includes(" ")) {
            formattedKeywords = formatKeywords(inputKeywords)
            console.log("Formatted keywords:", formattedKeywords)
          } else {
            formattedKeywords = inputKeywords
            console.log("No spaces found in inputKeywords.")
          }

          try {
            const browser = await playwright.launch({
              args: sparticuzChromium.args,

              executablePath: await sparticuzChromium.executablePath("https://github.com/Sparticuz/chromium/releases/download/v123.0.0/chromium-v123.0.0-pack.tar"),
              headless: sparticuzChromium.headless,
            })
            console.log("Chromium:", await browser.version())

            const context = await browser.newContext()
            console.log("new context")

            const page = await context.newPage()
            console.log("new page")
            await page.goto(amazonUrl)
            await page.waitForLoadState()
            await page.fill('input#twotabsearchtextbox', searchKeyword)
            await page.press('input#twotabsearchtextbox', 'Enter')
            await page.waitForLoadState()
            let targetUrl = page.url()
            console.log(`current_url: ${targetUrl}`)
            out.targetUrls.push(targetUrl)

            let loopNum = 0
            while (nextPageFlag) {
              await page.goto(targetUrl)
              await page.keyboard.press('PageDown')
              await new Promise((resolve) => setTimeout(resolve, 3000))
              await page.waitForLoadState()

              const hitCountElement = (
                await page.locator('.a-section.a-spacing-small.a-spacing-top-small').all()
              )[0].innerText()
              console.log(hitCountElement)

              const cards = await page.locator('.a-section.a-spacing-base').all()
              for (const [index, card] of cards.entries()) {
                loopNum++
                const indexPlus1 = index + 1
                const id = `${loopNum}_${out.targetUrls.length}_${indexPlus1}`
                const tempCard: Card = {
                  id,
                  imageUrl: '',
                  sponsored: false,
                  title: '',
                  stars: '',
                  ratingsCount: '',
                  salesText: '',
                  lastmonthsales: '',
                  price: '',
                  prePrice: '',
                  couponText: '',
                  prime: false,
                  primeicon: false,
                  url: '',
                }

                // imageUrl
                // imageUrl
                const imageElement = await card.locator('img.s-image').all()
                if (imageElement.length > 0) {
                  tempCard.imageUrl = await imageElement[imageElement.length - 1].getAttribute('src')
                }

                // sponsored
                const sponsoredElement = await card.locator('.puis-label-popover-default > .a-color-secondary')
                if (await sponsoredElement.isVisible()) {
                  const sponsoredText = await sponsoredElement.innerText()
                  if (sponsoredText === sponsoredLabels[locale]) {
                    tempCard.sponsored = true
                  }
                }

                // title
                const titleElement = await card.locator('.a-size-base-plus.a-color-base.a-text-normal')
                if (titleElement) {
                  tempCard.title = await titleElement.innerText()
                }

                // stars, ratingsCount
                const ariaLabelElements = await card.locator('.a-row.a-size-small > span').all()
                if (ariaLabelElements.length > 0) {
                  const starsText = await ariaLabelElements[0].getAttribute('aria-label')
                  if (starsText && starsText.includes('out of 5 stars')) {
                    tempCard.stars = starsText.replace(' out of 5 stars', '')
                  }

                  if (ariaLabelElements.length > 2) {
                    tempCard.ratingsCount = await ariaLabelElements[1]
                      .locator('div>span')
                      .getAttribute('aria-label')
                    if (tempCard.ratingsCount && tempCard.ratingsCount.includes('ratings')) {
                      tempCard.ratingsCount = tempCard.ratingsCount.replace(' ratings', '')
                    }
                  }
                } else {
                  console.log('No ratings found')
                }

                // sales
                const salesElement = await card.locator(
                  '[data-a-badge-color="sx-lightning-deal-red"].a-badge-label > .a-badge-label-inner.a-text-ellipsis'
                )
                if (await salesElement.isVisible()) {
                  tempCard.salesText = await salesElement.innerText()
                }

                // lastmonthsales
                const lastmonthsalesElement = await card.locator(
                  "div:nth-child(2) > div:nth-child(2) > div:nth-child(2) > .a-size-base"
                ).first()
                if (await lastmonthsalesElement.isVisible()) {
                  let lastmonthsalesText = await lastmonthsalesElement.innerText()
                  if (lastmonthsalesText && lastmonthsalesText.includes('bought in past month')) {
                    lastmonthsalesText = lastmonthsalesText.replace('+ bought in past month', '')
                  }
                  tempCard.lastmonthsales = lastmonthsalesText
                }

                // price
                const priceElement = await card.locator('.a-price-whole')
                if (await priceElement.isVisible()) {
                  tempCard.price = await priceElement.innerText()
                }

                // pre_price
                const prePriceElement = await card.locator(
                  '.a-price.a-text-price[data-a-strike="true"] > .a-offscreen'
                )
                if (await prePriceElement.isVisible()) {
                  tempCard.prePrice = await prePriceElement.innerText()
                }

                // coupon
                const couponElement = await card.locator('.s-coupon-unclipped')
                if (await couponElement.isVisible()) {
                  tempCard.couponText = await couponElement.innerText()
                }

                // prime
                const primeElement = await card.locator(
                  `[role="img"][aria-label="${primeLables[locale]}"]`
                )
                if (await primeElement.isVisible()) {
                  tempCard.prime = true
                }

                // prime
                const primeIconElement = await card.locator('.a-icon.a-icon-prime.a-icon-medium')
                if (await primeIconElement.isVisible()) {
                  const primeText = await primeIconElement.getAttribute('aria-label')
                  if (primeText === primeLables[locale]) {
                    tempCard.primeicon = true
                  }
                }

                // url
                const urlElement = await card.locator(
                  'a.a-link-normal.s-underline-text.s-underline-link-text.s-link-style.a-text-normal'
                ).all()
                if (urlElement.length > 0) {
                  let urlText = await urlElement[0].getAttribute('href')
                  if (urlText) {
                    if (urlText.includes('url=')) {
                      const splitStr = urlText.split('url=')[1]
                      urlText = fullyDecode(splitStr)
                    }
                    tempCard.url = amazonUrl + urlText
                  }
                }

                out.Cards.push(tempCard)

                console.log(`Listing counts: ${cards.length}`)

                // Pagination
                const paginationElement = await page.locator('span.s-pagination-strip')
                const currentPageElement = await paginationElement.locator('.s-pagination-selected')
                const currentPage = await currentPageElement.innerText()
                console.log(`Current page number: ${currentPage}`)

                const nextPageElement = await paginationElement.locator('.s-pagination-item.s-pagination-next')
                if (await nextPageElement.getAttribute('href')) {
                  targetUrl = amazonUrl + (await nextPageElement.getAttribute('href'))
                  nextPageFlag = true
                } else {
                  targetUrl = ''
                  nextPageFlag = false
                }
                console.log(`Next page: ${targetUrl}`)

                // if (devWritefileFlag) {
                //   const htmlContent = await page.content()
                //   console.log(`HTML content length: ${htmlContent.length}`)
                //   await fs.promises.writeFile(
                //     path.join(process.cwd(), `${searchKeyword}_output.html`),
                //     htmlContent,
                //     'utf8'
                //   )
                // }

                if (parseInt(currentPage) >= maxPage) {
                  nextPageFlag = false
                  console.log(`Max page: ${maxPage} process finished.`)
                  break
                }
              }

              await browser.close()

              const processingTime = Date.now() - startTime
              console.log(`Processing time (s): ${(processingTime / 1000).toFixed(1)}`)

              return JSON.stringify(out, null, 4)
            };

          } catch (error) {
            console.error('Navigation error:', error)
            // Handle the error appropriately
          }
        } else {
        }

        break
      case "PUT":
        // Update or create data in your database
        response.status(200).json({ id, name: name || `User ${id}` })
        break
      default:
        response.setHeader("Allow", ["GET", "PUT"])
        response.status(405).end(`Method ${method} Not Allowed`)
    }
  }
}