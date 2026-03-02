import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import urlparse

# -----------------------------
# 1. Your country list
# -----------------------------
target_countries = [
'Syrian Arab Republic','Indonesia','Colombia','Tunisia','Algeria',
'Afghanistan','Zimbabwe','United States of America',
'Iran (Islamic Republic of)','Morocco','Malaysia',
'Bolivia (Plurinational State of)','Iraq','Thailand',
'Democratic Republic of the Congo','Costa Rica','Honduras','Mexico',
'Nepal','India','Bulgaria','Cambodia','Ukraine','Georgia','Haiti',
'Gambia','Sierra Leone','Sudan','Uganda','China','Pakistan',
'Republic of Korea','Central African Republic','Cabo Verde','Japan',
'Myanmar','Equatorial Guinea','Taiwan (Province of China)','Romania',
'Nigeria','China, Hong Kong Special Administrative Region',
"Lao People's Democratic Republic",'Bangladesh','South Africa',
'Viet Nam','Philippines','United Republic of Tanzania','Somalia',
'Brazil','Croatia','Bosnia and Herzegovina','Italy','Argentina',
'Peru','Namibia','Botswana','Madagascar','Libya','Kenya','Malawi',
'Gabon','Spain','Dominican Republic','France','Yemen','Cameroon','Chad'
]

# -----------------------------
# 2. Normalize country names
# -----------------------------
def normalize_country(name):
    replacements = {
        "United States of America": "United States",
        "Iran (Islamic Republic of)": "Iran",
        "Bolivia (Plurinational State of)": "Bolivia",
        "Democratic Republic of the Congo": "Congo",
        "Republic of Korea": "South Korea",
        "Taiwan (Province of China)": "Taiwan",
        "China, Hong Kong Special Administrative Region": "Hong Kong",
        "Lao People's Democratic Republic": "Laos",
        "United Republic of Tanzania": "Tanzania",
        "Viet Nam": "Vietnam",
        "Syrian Arab Republic": "Syria",
        "Cabo Verde": "Cape Verde"
    }
    return replacements.get(name, name)

normalized_targets = [normalize_country(c) for c in target_countries]

# -----------------------------
# 3. Extract domain from URL
# -----------------------------
def extract_domain(url):
    """Extract just the domain from a URL (remove https://, www., etc.)"""
    if not url:
        return ""
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain
    except:
        return url

# -----------------------------
# 4. Continent URLs
# -----------------------------
continent_urls = {
    "Europe": "https://worldnewspaperlist.com/europe",
    "North America": "https://worldnewspaperlist.com/north-america",
    "South America": "https://worldnewspaperlist.com/south-america",
    "Asia": "https://worldnewspaperlist.com/asia",
    "Africa": "https://worldnewspaperlist.com/africa",
    "Australia & Oceania": "https://worldnewspaperlist.com/australia-and-oceania"
}

# -----------------------------
# 5. Storage list
# -----------------------------
data = []

headers = {
    "User-Agent": "Mozilla/5.0"
}

# -----------------------------
# 6. Loop through continents
# -----------------------------
for continent, url in continent_urls.items():
    print(f"\nScraping continent: {continent}")
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    country_links = soup.find_all("a")

    for link in country_links:
        country_name = link.text.strip()

        if country_name in normalized_targets:
            country_url = link.get("href")
            
            if not country_url.startswith("http"):
                country_url = "https://worldnewspaperlist.com" + country_url

            print(f"  -> Scraping {country_name}")

            country_response = requests.get(country_url, headers=headers)
            country_soup = BeautifulSoup(country_response.text, "html.parser")

            current_h2 = None
            current_h3 = None

            # Go through page structure in order
            for tag in country_soup.find_all(["h2", "h3", "a"]):

                if tag.name == "h2":
                    current_h2 = tag.get_text(strip=True)

                elif tag.name == "h3":
                    current_h3 = tag.get_text(strip=True)

                elif tag.name == "a":
                    newspaper_name = tag.get_text(strip=True)
                    newspaper_url = tag.get("href", "")

                    if newspaper_name and current_h2 and current_h3:
                        # Exclude the unwanted h2 category
                        if current_h2 != "Newspapers and news media list by Continent":
                            data.append({
                                "Region": continent,
                                "Country": country_name,
                                "Category (h2)": current_h2,
                                "Subcategory (h3)": current_h3,
                                "Newspaper": newspaper_name,
                                "URL": newspaper_url
                            })

            time.sleep(1)  # polite delay

# -----------------------------
# 7. Convert to DataFrame and restructure
# -----------------------------
df = pd.DataFrame(data)

# Group by Region, Country, and Category (h2) only
grouped_data = []

for (region, country, category), group in df.groupby(["Region", "Country", "Category (h2)"]):
    # Create a dictionary of unique newspaper:domain pairs
    newspaper_dict = {}
    seen_names = set()
    seen_domains = set()
    
    for _, row in group.iterrows():
        name = row["Newspaper"]
        url = row["URL"]
        domain = extract_domain(url)
        
        # Skip if we've already seen this name or domain (avoid duplicates)
        if name in seen_names or (domain and domain in seen_domains):
            continue
        
        newspaper_dict[name] = domain
        seen_names.add(name)
        if domain:
            seen_domains.add(domain)
    
    # Format as "Name: domain, Name2: domain2, ..."
    newspapers_str = ", ".join([f"{name}: {domain}" for name, domain in newspaper_dict.items()])
    
    # Count the number of newspapers
    newspaper_count = len(newspaper_dict)
    
    grouped_data.append({
        "Region": region,
        "Country": country,
        "Category (h2)": category,
        "Newspapers": newspapers_str,
        "Count": newspaper_count
    })

df_final = pd.DataFrame(grouped_data)

# -----------------------------
# 8. Save file
# -----------------------------
df_final.to_csv("world_newspapers_filtered2.csv", index=False)

print("\nDone! Data saved as world_newspapers_filtered2.csv")
print(f"Total rows: {len(df_final)}")
print(df_final.head(10))

