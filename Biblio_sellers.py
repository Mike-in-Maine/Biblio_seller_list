# Scrapes all sellers on Biblio.com with:
# - Name, ID, total number of books and seller rating (stars)
# - Exports a csv called "scraped_data.csv"
# Uses scrape.do technology.

import csv
import re
import urllib
import urllib.parse
import badpeople
from bs4 import BeautifulSoup
import pandas as pd
import requests

seller_names = []
seller_ids = []
seller_ratings = []
seller_states = []
seller_citys = []
number_of_books = []
member_since_years = []
shippings = []


def out_through_scrapedo(link):
    try:
        token = badpeople.api_key[1]
        target_url = urllib.parse.quote(link)
        render = "true"
        url_scrapedo = "https://api.scrape.do/?token={}&geoCode=us&super=false&url={}".format(token, target_url, render)
        html = requests.request("GET", url_scrapedo, timeout=120)
        return html
    except Exception as e:
        print(e)
        print("Scrape.do timed out. Working on next ISBN")

def scrape_data_from_seller_page(link): #The page with all the books available

    dealer_id_number = re.search(r"dealer_id=(\d+)", link)
    print(link)
    print(dealer_id_number)
    print(dealer_id_number.group(1))
    seller_ids.append(dealer_id_number.group(1))
    html_seller_result = out_through_scrapedo(link)
    seller_data_page = BeautifulSoup(html_seller_result.text, 'html.parser')
    # print(seller_data_page.text)
    try:
        books_avail_number = int(re.search(r'of (\d+)', seller_data_page.find('div', class_="results-count").get_text()).group(1))
        number_of_books.append(books_avail_number)
    except:
        number_of_books.append("unknown")
    try:
        seller_name = seller_data_page.find('span', class_='subhead').get_text(strip=True).replace("Books from ", "") if seller_data_page.find('span', class_='subhead') else None
        seller_names.append(seller_name)
    except:
        seller_names.append("unknown")

    try:
        seller_rating = int(re.search(r'\b\d\b', seller_data_page.find('div', class_='speech').get_text()).group())
        seller_ratings.append(seller_rating)
    except:
        seller_ratings.append("unknown")
    try:
        shipping = seller_data_page.find_all('span', class_='nowrap')[-1].get_text(strip=True).replace('$', '') if seller_data_page and '$' in seller_data_page.text else "0" if seller_data_page else None
    except:
        shipping = '0'

    shippings.append(shipping)

    print(seller_names)
    print(seller_ids)
    print(seller_ratings)
    print(number_of_books)
    print(shippings)

    return seller_names, seller_ids, seller_ratings, number_of_books, shippings

def get_dealer_id():
    link = 'https://www.biblio.com/bookstores/united-states/'
    #link = 'https://www.biblio.com/bookstores/united-states/alabama'
    html_result = out_through_scrapedo(link)
    soup = BeautifulSoup(html_result.text, 'html.parser')
    us_states = soup.find('ul', class_='big-list text-cols four').find_all('li')

    for us_state in us_states[46:]:
        print(us_states)
        state_soup = BeautifulSoup(str(us_state), 'html.parser')
        link = state_soup.a['href']
        last_word = link.split("/")[-1]

        #if link != "https://www.biblio.com/bookstores/united-states/nevada":
            #break
        print('US State: ', link)
        html_state_result = out_through_scrapedo(link) #clicking on each state
        if html_state_result:
            state_soup = BeautifulSoup(html_state_result.text, 'html.parser')
            try:
                #state_soup.find('ul', class_=re.compile(r'big-list text-cols (two|three|four)')).find_all('li'):
                state_link = state_soup.find('ul', class_=re.compile(r'big-list text-cols (two|three|four)')).find_all('li') #when states have more than one city
                print("Found multiple cities")
                #print(state_link)  # Process the state page here to extract dealer IDs or any other information
                for city in state_link: # assuming one state has more cities
                    city_soup = BeautifulSoup(str(city), 'html.parser')
                    link = city_soup.a['href']
                    print('us, states, cities: ', link)
                    html_city_result = out_through_scrapedo(link) #clicking on each city and there can be 2 cases: 1) only one seller in that city or 2) multiple sellers in that city
                    city_soup = BeautifulSoup(html_city_result.text, 'html.parser')
                    #print(city_soup)
                    # Case 1, multiple sellers in the city page

                    if city_soup.find('div', class_="summary bookseller"):
                        print("1Found multiple sellers in one city")
                        seller_div = city_soup.find('div', class_="summary bookseller")
                        link_to_seller = seller_div.find_all('h3')
                        #print(link_to_seller)
                        href_value = [h3.a['href'] for h3 in link_to_seller]
                        print("1:",href_value)
                        for link in href_value:
                            html_seller_result = out_through_scrapedo(link)
                            seller_soup = BeautifulSoup(html_seller_result.text, 'html.parser')
                            warning_element = seller_soup.find('h3', class_='warning')
                            print("1warning:", warning_element)
                            if warning_element:
                                continue
                            member_since_div = seller_soup.find('div', class_="splat")
                            strong_tag = member_since_div.find('strong')
                            member_since = strong_tag.get_text()
                            member_since_years.append(member_since)
                            print("1Member since: ", member_since)

                            single_seller_in_city = seller_soup.find('div', class_="browse-all mt-3 mb-4")
                            # print(single_seller_in_city)
                            link2 = single_seller_in_city.find('a')
                            link = link2.get('href')
                            print("1Seller link going to get detail data: ",link)
                            scrape_data_from_seller_page(link)

                    # Case 2 only one seller in that city

                    elif city_soup.find('div', class_="browse-all mt-3 mb-4"):

                        single_seller_in_city = city_soup.find('div', class_="browse-all mt-3 mb-4")
                        #print(single_seller_in_city)
                        link2 = single_seller_in_city.find('a')
                        link = link2.get('href')
                        print(link)
                        warning_element = single_seller_in_city.find('h3', class_='warning')
                        if warning_element:
                            continue
                        member_since_div = city_soup.find('div', class_="splat")
                        strong_tag = member_since_div.find('strong')
                        member_since = strong_tag.get_text()
                        member_since_years.append(member_since)
                        print("2Member since: ", member_since)
                        print("2Single City: ", link)
                        single_seller_in_city = city_soup.find('div', class_="browse-all mt-3 mb-4")
                        # print(single_seller_in_city)
                        link2 = single_seller_in_city.find('a')
                        link = link2.get('href')
                        print("2Seller link going to get detail data: ", link)
                        scrape_data_from_seller_page(link)


            except: #if state has no cities but a list of all sellers on one page.
                # case 1, multiple sellers in the city page
                print("3Found one city with multiple sellers like Alaska")
                seller_div = state_soup.find('div', class_="summary bookseller")

                #href_value = [h3.a['href'] for h3 in link_to_seller]
                #print(seller_div.text)
                link_to_seller = seller_div.find_all('h3')

                # print(link_to_seller)
                href_value = [h3.a['href'] for h3 in link_to_seller]
                print(href_value)
                for link in href_value:
                    html_seller_result = out_through_scrapedo(link)
                    seller_soup = BeautifulSoup(html_seller_result.text, 'html.parser')
                    warning_element = seller_soup.find('h3', class_='warning')
                    print("1warning:", warning_element)
                    if warning_element:
                        continue
                    member_since_div = seller_soup.find('div', class_="splat")

                    strong_tag = member_since_div.find('strong')
                    member_since = strong_tag.get_text()
                    member_since_years.append(member_since)
                    print("3Member since: ", member_since)
                    single_seller_in_city = seller_soup.find('div', class_="browse-all mt-3 mb-4")
                    # print(single_seller_in_city)
                    link2 = single_seller_in_city.find('a')
                    link = link2.get('href')
                    print("1Seller link going to get detail data: ", link)
                    scrape_data_from_seller_page(link)

        else:
            print("Failed to fetch state page for:", link)

        lengths = {
            'Seller Name': len(seller_names),
            'Seller ID': len(seller_ids),
            'Seller Rating': len(seller_ratings),
            'Member Since': len(member_since_years),
            'Shipping': len(shippings),
            # 'Seller State': len(seller_states),
            # 'Seller City': len(seller_citys),
            'Number of Books': len(number_of_books)
        }

        print("Lengths of lists:")
        for key, value in lengths.items():
            print(f"{key}: {value}")

        # Check if all lengths are the same
        if len(set(lengths.values())) == 1:
            print("All lists have the same length.")
        else:
            print("Lengths of lists are not the same.")

        df = pd.DataFrame({
            'Seller Name': seller_names,
            'Seller ID': seller_ids,
            'Seller Rating': seller_ratings,
            'Member Since': member_since_years,
            'Shipping': shippings,
            # 'Seller State': seller_states,
            # 'Seller City': seller_citys,
            'Number of Books': number_of_books
        })

        csv_file_path = f'{last_word}scraped_data.csv'
        df.to_csv(csv_file_path, index=False, encoding='utf-8')


get_dealer_id()






