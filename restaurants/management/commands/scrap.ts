import { chromium } from 'playwright'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const scrapDorm = async () => {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();
    console.log('Navigating to the list page...');
    const link = 'https://dorm2.khu.ac.kr/50/5030.do#'
    await page.goto(link);
    await Promise.all([
        page.waitForNavigation({ waitUntil: 'domcontentloaded' }),
        page.locator('a').filter({ hasText: '전체보기' }).first().click()
    ]);
    await page.waitForSelector('td.te_left');
    const menuTexts = await page.locator('td.te_left').allInnerTexts();
    console.log(menuTexts);
    console.log(menuTexts.length);
    await browser.close();
}
const scrapHufs = async (isStudent: boolean) => {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();

    console.log('Navigating to the list page...');
    const link = isStudent ? 'https://www.hufs.ac.kr/hufs/11318/subview.do#click' : 'https://www.hufs.ac.kr/hufs/11318/subview.do?enc=Zm5jdDF8QEB8JTJGY2FmZXRlcmlhJTJGaHVmcyUyRjElMkZ2aWV3LmRvJTNGeWVhciUzRDIwMjYlMjZtb250aCUzRDA1JTI2c2VsRGF0ZSUzRDIwMjYwNTIxJTI2c2VsQ2FmSWQlM0RoMTAyJTI2';
    await page.goto(link);
    await page.waitForSelector('td.no-menu, td.menu');
    const menuTexts = await page.locator('td.no-menu, td.menu').allInnerTexts();
    console.log(menuTexts);
    console.log(menuTexts.length);

    await browser.close();
}
const scrap = async (isSeoul: boolean) => {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();

    console.log('Navigating to the list page...');
    const link = isSeoul ? 'https://www.khu.ac.kr/kor/user/bbs/BMSR00040/list.do?menuNo=200283&catId=136' : 'https://www.khu.ac.kr/kor/user/bbs/BMSR00040/list.do?menuNo=200283&catId=137';
    await page.goto(link);
    await page.waitForSelector('tbody');

    // Find links in tbody. 
    // On many BBS pages, the links are actually javascript:view('...') calls.
    // Let's try to get all 'a' in tbody and handle them.
    const rawLinks = await page.$$eval('tbody a', (elements, isSeoul) => {
        const locations = isSeoul ? ['푸른솔', '청운관'] : ['학생회관']
        return locations.map(loc => {
            const el = elements.find(el => el.innerText.includes(loc));
            return ({
                href: el?.href,
                text: el?.innerText.trim(),
                onclick: el?.getAttribute('onclick')
            })
        })
        // elements.map(el => {
        //     if (locations.some(loc => el.innerText.includes(loc))) {
        //         locations = locations.filter(loc => !el.innerText.includes(loc));
        //         return ({
        //             href: el.href,
        //             text: el.innerText.trim(),
        //             onclick: el.getAttribute('onclick')
        //         })
        //     } else return null
        // }).filter(link => link !== null)

        // elements.map(el => ({
        //     href: el.href,
        //     text: el.innerText.trim(),
        //     onclick: el.getAttribute('onclick')
        // })).slice(0, 2)

    }, isSeoul);

    console.log(`Found ${rawLinks.length} links in tbody.`);

    const downloadDir = path.join(__dirname, 'downloads');
    if (!fs.existsSync(downloadDir)) {
        fs.mkdirSync(downloadDir);
    }

    for (const linkData of rawLinks) {
        if (!linkData.href || linkData.href.startsWith('javascript:')) {
            // If it's a javascript link, we might need a different approach, 
            // but for KHU BBS, usually the title link navigates.
            // Let's try to click it if href is not a direct URL.
            console.log(`Handling link: ${linkData.text}`);

            // Re-navigating to the list page might be needed if we navigated away
            if (page.url() !== link) {
                await page.goto(link);
                await page.waitForSelector('tbody');
            }

            // Click the link by text to trigger navigation
            try {
                await Promise.all([
                    page.waitForNavigation({ waitUntil: 'domcontentloaded' }),
                    page.locator('tbody a').filter({ hasText: linkData.text }).first().click()
                ]);
            } catch (err) {
                console.error(`Failed to navigate to ${linkData.text}: ${err.message}`);
                continue;
            }
        } else {
            console.log(`Visiting URL: ${linkData.href}`);
            try {
                await page.goto(linkData.href, { waitUntil: 'domcontentloaded' });
            } catch (err) {
                console.error(`Failed to visit ${linkData.href}: ${err.message}`);
                continue;
            }
        }
        const title = await page.$eval('p.txt06', p => p.innerText.trim());
        // Now on the detail page, find PNG images
        const images = await page.$$eval('img', imgs =>
            imgs.map(img => img.src).filter(src => src.endsWith('.png') && !src.includes('decoGnb') && !src.includes('footLogo') && !src.includes('ico'))
        );

        console.log(`Found ${images.length} PNG images on this page.`);

        for (const imgUrl of images) {
            try {
                // Ensure imgUrl is absolute
                const absoluteImgUrl = new URL(imgUrl, page.url()).href;
                // const urlParsed = new URL(absoluteImgUrl);
                const imageName = title.includes('청운관') ? 'c.png' : title.includes('푸른솔') ? 'p.png' : 'h.png';
                const localPath = path.join(downloadDir, imageName);

                const response = await page.request.get(absoluteImgUrl);
                if (response.status() === 200) {
                    const buffer = await response.body();
                    fs.writeFileSync(localPath, buffer);
                    console.log(`Downloaded: ${imageName}`);
                }
            } catch (err) {
                console.error(`Failed to download image ${imgUrl}: ${err.message}`);
            }
        }

        // Go back to the list page for the next item
        await page.goto('https://www.khu.ac.kr/kor/user/bbs/BMSR00040/list.do?menuNo=200283');
        await page.waitForSelector('tbody');
    }

    await browser.close();
    console.log('Done.');
    return true;
}

// scrap(true)
// scrapHufs(true)
// scrapDorm()
export default scrap