import { gotScraping } from "got-scraping";

async function scrapePlace(url, cookies, query) {
  try {
    const cookieString = Object.entries(cookies)
      .map(([key, value]) => `${key}=${value}`)
      .join("; ");

    const response = await gotScraping({
      url: url,
      timeout: {
        request: 12000,
      },
      headers: {
        Cookie: cookieString,
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
      },
    });

    const html = response.body;
    const result = extractTitle(html);

    return {
      nama: result.nama,
      alamat: result.alamat,
      telepon: result.telepon,
      kategori: result.kategori,
      pemilik: result.pemilik,
      link: url,
      query: query,
    };
  } catch (error) {
    console.error(`Error scraping ${url}:`, error.message);
    return {
      nama: null,
      alamat: null,
      telepon: null,
      kategori: null,
      pemilik: null,
      link: url,
      query: query,
      error: error.message,
    };
  }
}

function extractTitle(html) {
  try {
    const parts = html.split(";window.APP_INITIALIZATION_STATE=");
    if (parts.length < 2) {
      return {
        nama: null,
        alamat: null,
        telepon: null,
        kategori: null,
        pemilik: null,
      };
    }

    const secondPart = parts[1].split(";window.APP_FLAGS")[0];
    const rawData = JSON.parse(secondPart)[3][6];

    if (!rawData.startsWith(")]}'")) {
      return {
        nama: null,
        alamat: null,
        telepon: null,
        kategori: null,
        pemilik: null,
      };
    }

    const cleaned = rawData.substring(5);
    const parsedData = JSON.parse(cleaned);

    const nama = parsedData[6]?.[11] || null;
    const alamat = parsedData[6]?.[39] || null;
    const telepon = parsedData[6]?.[178]?.[0]?.[3] || null;
    const kategori = parsedData[6]?.[13] || null;
    const pemilik = parsedData[6]?.[57]?.[1] || null;

    return { nama, alamat, telepon, kategori, pemilik };
  } catch (error) {
    return {
      nama: null,
      alamat: null,
      telepon: null,
      kategori: null,
      pemilik: null,
    };
  }
}

// Handle command line arguments
async function main() {
  const args = process.argv.slice(2);
  if (args.length < 3) {
    console.error("Usage: node scraper_node.js <url> <cookies_json> <query>");
    process.exit(1);
  }

  const url = args[0];
  const cookiesJson = args[1];
  const query = args[2];

  let cookies;
  try {
    cookies = JSON.parse(cookiesJson);
  } catch (error) {
    console.error("Invalid cookies JSON:", error.message);
    process.exit(1);
  }

  const result = await scrapePlace(url, cookies, query);
  console.log(JSON.stringify(result));
}

// Check if this file is being run directly
import { fileURLToPath } from "url";
import { dirname } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

if (process.argv[1] === __filename) {
  main().catch((error) => {
    console.error("Unhandled error:", error);
    process.exit(1);
  });
}

export { scrapePlace };
