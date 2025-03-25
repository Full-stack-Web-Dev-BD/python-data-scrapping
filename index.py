from selenium import webdriver
import sqlite3
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

    # Safely convert all scraped elements to strings
    product_name = soup.find('h1', id='prd_name').text.strip() if soup.find('h1', id='prd_name') else 'N/A'
    product_price = soup.find('span', id='prc_id').text.strip() if soup.find('span', id='prc_id') else 'N/A'
    image_url = soup.find('img', id='prdimgdiv')['src'] if soup.find('img', id='prdimgdiv') else 'N/A'
    description_text = soup.find('div', class_='mt10 fs14 lh1-7 pr desc_5ln pdp_desc').text.strip() if soup.find('div', class_='mt10 fs14 lh1-7 pr desc_5ln pdp_desc') else 'N/A'
    
    properties = {}
    product_id = ''
    match = re.search(r"[\?&]id=(\d+)", product_url)
    if match:
        product_id = match.group(1)

    company_name = soup.find('h2', class_='fs17 fw6 clr2 lh19').text.strip() if soup.find('h2', class_='fs17 fw6 clr2 lh19') else 'N/A'
    company_logo = soup.find('img', alt=company_name)['src'] if soup.find('img', alt=company_name) else 'N/A'
    location = soup.find('span', class_='lne2txt ofh clr2').text.strip() if soup.find('span', class_='lne2txt ofh clr2') else 'N/A'
    review_count = soup.find('span', class_='tcund').text.strip() if soup.find('span', class_='tcund') else 'N/A'
    gst_number = soup.find('span', class_='clr9').text.strip() if soup.find('span', class_='clr9') else 'N/A'
    # iec_number = soup.find('span', class_='clr2').text.strip() if soup.find('span', class_='clr2') else 'N/A'
    # iec_number = soup.find('span', class_='clr2').text.strip()
    verified_status = 'Verified' if soup.find('span', class_='fw6') else 'Not Verified'
    trustseal_link = soup.find('span', class_='slrsp slrM fsh0 slr2')['onclick'].split("'")[1] if soup.find('span', class_='slrsp slrM fsh0 slr2') else 'N/A'

    supplier_info = {
        'company_name': company_name,
        'company_logo': company_logo,
        'location': location,
        'review_count': review_count,
        'gst_number': gst_number,
        # 'iec_number': iec_number,
        'verified_status': verified_status,
        'trustseal_link': trustseal_link
    }

    rows = soup.find_all('tr', id='desc_sku')
    for row in rows:
        cells = row.find_all('td')
        if len(cells) == 2:
            key = cells[0].text.strip()
            value = cells[1].text.strip()
            properties[key] = value

    product_details = {
        'product_id': product_id,
        'product_name': product_name,
        'description': description_text,
        'product_price': product_price,
        'image_URL': image_url,
        'properties': properties,
        'supplier_info': supplier_info
    }

    print("Scraped Product:", product_id)
    product_details_list.append(product_details)

# Iterate through the links and extract the product URLs
for link in product_links:
    href = link['href']
    # Check if the href contains the desired pattern for the product detail page
    if href.startswith("products/?id="):
        product_url = f"https://export.indiamart.com/{href}"
        get_product_details(product_url)




# Print the list of URLs as a comma-separated string
print("Total Product Found", len(product_details_list))

# Save the scraped data to a JSON file
with open("product_data.json", "w", encoding="utf-8") as json_file:
    json.dump(product_details_list, json_file, indent=4, ensure_ascii=False)




import json

# Define the output SQL file name
sql_file_name = "product_data.sql"

with open(sql_file_name, "w", encoding="utf-8") as sql_file:
    # Write the SQL command to create the table
    sql_file.write("CREATE TABLE IF NOT EXISTS products (\n")
    sql_file.write("    product_id TEXT PRIMARY KEY,\n")
    sql_file.write("    product_name TEXT,\n")
    sql_file.write("    description TEXT,\n")
    sql_file.write("    product_price TEXT,\n")
    sql_file.write("    image_URL TEXT,\n")
    sql_file.write("    properties TEXT,\n")
    sql_file.write("    supplier_info TEXT\n")
    sql_file.write(");\n\n")
    
    # Loop over the product details and write an INSERT statement for each
    for product in product_details_list:
        # Convert dictionaries to JSON strings for properties and supplier_info
        properties_json = json.dumps(product['properties'])
        supplier_info_json = json.dumps(product['supplier_info'])
        
        # Replace single quotes in text fields to avoid SQL errors
        product_id = product['product_id'].replace("'", "''")
        product_name = product['product_name'].replace("'", "''")
        description = product['description'].replace("'", "''")
        product_price = product['product_price'].replace("'", "''")
        image_URL = product['image_URL'].replace("'", "''")
        properties_json = properties_json.replace("'", "''")
        supplier_info_json = supplier_info_json.replace("'", "''")
        
        # Write the INSERT statement
        sql_file.write(
            f"INSERT INTO products (product_id, product_name, description, product_price, image_URL, properties, supplier_info) "
            f"VALUES ('{product_id}', '{product_name}', '{description}', '{product_price}', '{image_URL}', '{properties_json}', '{supplier_info_json}');\n"
        )

print(f"Data saved to SQL file '{sql_file_name}' successfully!")

print("Data saved to product_data.json successfully!")
# Close the browser after scraping
driver.quit()
