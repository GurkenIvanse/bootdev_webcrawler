from urllib.parse import urlsplit, urljoin
from bs4 import BeautifulSoup, Tag
from typing import TypedDict
import requests

class PageData(TypedDict):
    url: str
    heading: str
    first_paragraph: str
    outgoing_links: list[str]
    image_urls: list[str]

def get_html(url):
    response = requests.get(url, headers={"User-Agent": "BootCrawler/1.0"})
    if response.status_code > 400:
        raise Exception(f"Response:{response.status_code}")
    if "text/html" not in response.headers["Content-Type"]:
        raise Exception(f"text/html not in Content")

    return response.text

def craw_page(base_url, current_url=None, page_data=None):
    if page_data == None:
        page_data = {}
    if current_url == None:
        current_url = base_url
    base   = urlsplit(base_url)
    current= urlsplit(current_url)

    if base.netloc != current.netloc:
        return
    if current_url != None:
        norm_current = normalize_url(current_url)
    if page_data != None:
        if norm_current in page_data:
            return
    print("getting the html")
    #print(f"{base_url} and {norm_current}")
    extracted_html = get_html(current_url)
    extracted_page:PageData = extract_page_data(extracted_html,current_url)
    page_data[norm_current] = extracted_page
    print(f"{page_data}")
    for v in extracted_page["outgoing_links"]:
        craw_page(base_url,v,page_data)
    return page_data

def normalize_url(url: str)-> str:
    o = urlsplit(url)
    path = o.path
    #print(f"Path:{o}")

    if path == "":
        return o.scheme+"://"+ o.netloc
    if path[len(path)-1] == "/":
        #print(f"Hallo:{path[0:len(path)-1]}")
        path = path[0:len(path)-1]
    if o.scheme == "":
        return o.netloc + path
    return o.netloc + path

def get_heading_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    h_tag = soup.find("h1")
    if h_tag is None:
        h_tag = soup.find("h2")

    return h_tag.get_text(strip=True) if isinstance(h_tag, Tag) else ""

def get_first_paragraph_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    h_tag = soup.find("main")
    if h_tag is not None:
        h_tag = h_tag.find("p")
    else:
        h_tag = soup.find("p")
    return h_tag.get_text(strip=True) if isinstance(h_tag, Tag) else ""

def get_urls_from_html(body:str, url:str)->list[str]:
    res: list[str] = []
    soup = BeautifulSoup(body, "html.parser")
    
    for l in soup.find_all("a"):
        link = l.get("href")
        #print(f"Link:{link}")
        if link is None:
            return res
        o = urlsplit(link)
        #print(f"Result:{o}")
        if o.path == "":
            path = ""
        else:
            path = o.path
        u = urljoin(url,path)
        res.append(u)
    return res

def get_images_from_html(html:str, base_url:str):
    res: list[str] = []
    soup = BeautifulSoup(html, "html.parser")

    for l in soup.find_all("img"):
        img = l.get("src")
        if img is None:
            return res
        o = urlsplit(img)
        if o.path == "":
            path = ""
        else:
            path = o.path
        u = urljoin(base_url,path)
        res.append(u)
    return res

def extract_page_data(html: str, page_url: str)->PageData:

    data : PageData = {}

    data['url'] = page_url
    data['heading'] = get_heading_from_html(html)
    data['first_paragraph']  = get_first_paragraph_from_html(html)
    data['outgoing_links'] = get_urls_from_html(html,page_url)
    data['image_urls'] = get_images_from_html(html, page_url)

    return data

