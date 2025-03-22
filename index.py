from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import requests
import re
import json

# Set up the service and options
service = Service(r"C:\Program Files\gekodriver\geckodriver.exe")
firefox_options = Options()
firefox_options.headless = True  # Run in headless mode (no UI)

# Initialize the Firefox driver
driver = webdriver.Firefox(service=service, options=firefox_options)

# Navigate to the website
url = "https://export.indiamart.com/search.php?ss=sarees&tags=res:RC4|ktp:N0|stype:attr=1|mtp:G|wc:1|qr_nm:gd|cs:8100|com-cf:nl|ptrs:na|mc:10950|cat:224|qry_typ:P|lang:en"
driver.get(url)

# Wait for the page to load completely (optional, if necessary)
driver.implicitly_wait(10)  # Wait for up to 10 seconds

# Get the HTML source
html_source = driver.page_source

# Optionally, use BeautifulSoup to parse the HTML content
soup = BeautifulSoup(html_source, 'html.parser')

# Find all the product links using the appropriate class
product_links = soup.find_all('a', href=True)

# Create an array to store the URLs
urls = []
page_count=0


product_details_list = []


def get_product_details(product_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(product_url, headers=headers)
    if response.status_code != 200:
        print("Failed to retrieve the product page.")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    product_name = soup.find('h1', id='prd_name')
    product_id=''
    product_price = soup.find('span', id='prc_id').text
    image_url = soup.find('img', id='prdimgdiv')['src']
    description_text = soup.find('div', class_='mt10 fs14 lh1-7 pr desc_5ln pdp_desc').text.strip() if soup.find('div', class_='mt10 fs14 lh1-7 pr desc_5ln pdp_desc') else 'N/A'
    properties = {}
    # Using regular expression to extract the ID after "id="
    match = re.search(r"[\?&]id=(\d+)", product_url)
    if match:
        product_id = match.group(1)
    else:
        pass
    # Extracting company name and logo
    company_name = soup.find('h2', class_='fs17 fw6 clr2 lh19').text.strip() if soup.find('h2', class_='fs17 fw6 clr2 lh19') else 'N/A'
    company_logo = soup.find('img', alt=company_name)['src'] if soup.find('img', alt=company_name) else 'N/A'
    
    # Extracting location
    location = soup.find('span', class_='lne2txt ofh clr2').text.strip() if soup.find('span', class_='lne2txt ofh clr2') else 'N/A'
    
    # Extracting rating and review count
    # rating = soup.find('span', class_='fw7').text.strip() if soup.find('span', class_='fw7') else 'N/A'
    review_count = soup.find('span', class_='tcund').text.strip() if soup.find('span', class_='tcund') else 'N/A'
    
    # Extracting GST number and IEC number
    gst_number = soup.find('span', class_='clr9').text.strip() if soup.find('span', class_='clr9') else 'N/A'
    iec_number = soup.find('span', class_='clr2').text.strip() if soup.find('span', class_='clr2') else 'N/A'
    
    # Extracting verified status and trustseal link
    verified_status = 'Verified' if soup.find('span', class_='fw6') else 'Not Verified'
    trustseal_link = soup.find('span', class_='slrsp slrM fsh0 slr2')['onclick'].split("'")[1] if soup.find('span', class_='slrsp slrM fsh0 slr2') else 'N/A'
    
    # Storing all the information in supplier_info dictionary
    supplier_info = {
        'company_name': company_name,
        'company_logo': company_logo,
        'location': location,
        # 'rating': rating,
        'review_count': review_count,
        'gst_number': gst_number,
        'iec_number': iec_number,
        'verified_status': verified_status,
        'trustseal_link': trustseal_link
    }
    # Find all relevant table rows
    rows = soup.find_all('tr', id='desc_sku')
    for row in rows:
        cells = row.find_all('td')
        key = cells[0].text.strip()  # Attribute name
        value = cells[1].text.strip()  # Attribute value
        properties[key] = value
    # product details object
    product_details = {
        'product_id':product_id,
        'product_Name': product_name,
        'description':description_text,
        'product_price': product_price,
        'image_URL': image_url,
        'properties': properties,
        'supplier_info':supplier_info
    }
    
    # Print the final object
    print("Scrapped  Product : ", product_id)
    product_details_list.append(product_details)

# Iterate through the links and extract the product URLs
for link in product_links:
    href = link['href']
    # Check if the href contains the desired pattern for the product detail page
    if href.startswith("products/?id="):
        product_url = f"https://export.indiamart.com/{href}"
        urls.append(f'"{product_url}"')
        get_product_details(product_url)




# Print the list of URLs as a comma-separated string
print("Total Product Fined", len(urls))

with open('product_details.txt', 'w', encoding='utf-8') as txt_file:
    txt_file.write(str(product_details_list))
# Close the browser after scraping
driver.quit()
