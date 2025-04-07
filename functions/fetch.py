import requests
from bs4 import BeautifulSoup
import json

def rget_page(url):
    page = requests.get(url)
    soap = BeautifulSoup(page.text, 'html.parser')
    return soap

def get_springer(soap):
    dois = []
    for entry in soap.find_all("h3", attrs={"class": "app-card-open__heading"}):
        a = entry.find('a')
        dois.append(a['href'])
        
    return dois
    

def get_arxiv(soap):
    dois = []
    for entry in soap.find_all("p", attrs={"class": "list-title is-inline-block"}):
        a = entry.find('a')
        dois.append(a.text)
        
    return dois

def get_ieee(soap):
    names = []
    for entry in soap.find_all("h3", attrs={"class": "result-item-title"}):
        a = entry.find('a')
        if(not a):
            continue
        name = " ".join(a.text.split())
        names.append(name)
        
    return names

def get_acm(soap):
    dois = []
    for entry in soap.find_all("li", attrs={"class": "issue-item-container"}):
        a = entry.find('a', attrs={'class': "issue-item__doi"})
        t = entry.find('div', attrs={'class': 'issue-heading'})
        if(a and t):
            dois.append({
                "doi": a.text,
                "content": t.text
            })
        
    return dois

def save(text, name):
    with open(name, 'w') as f:
        f.write(text)
        
def semantic_scholar_from_doi(dois, size=100):
    data = []

    for i in range(0, len(dois), size):
        print(f"Batch: {i}")
        r = requests.post(
            'https://api.semanticscholar.org/graph/v1/paper/batch',
            params={'fields': 'title,abstract,publicationDate'},
            json={"ids": dois[i:i+size]}
        )
        print(r)
        data.append(r.text)
    
    # final = [paper for batch in data for paper in json.loads(batch)]
    # return final
    return data

def semantic_scholar_err(dois, data, err, size=100):
    for i in err:
        print(f"Batch: {i}")
        r = requests.post(
            'https://api.semanticscholar.org/graph/v1/paper/batch',
            params={'fields': 'title,abstract'},
            json={"ids": dois[i:i+size]}
        )
        print(r)
        data[i] = r.text
    return data