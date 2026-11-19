import json, urllib.parse, urllib.request
UA={"User-Agent":"TurkiyeKesif/1.0 (demo)"}
def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40))
def wiki_coords(name, lang="tr"):
    s = get("https://%s.wikipedia.org/w/api.php?" % lang + urllib.parse.urlencode({
        "action":"query","list":"search","srsearch":name,"srlimit":3,"format":"json"}))
    titles=[x["title"] for x in s["query"]["search"]]
    if not titles: return None, []
    d = get("https://%s.wikipedia.org/w/api.php?" % lang + urllib.parse.urlencode({
        "action":"query","prop":"coordinates","titles":"|".join(titles),"format":"json","redirects":1}))
    for pid,page in d["query"]["pages"].items():
        c = page.get("coordinates")
        if c: return (c[0]["lat"], c[0]["lon"]), titles
    return None, titles
for n in ["Düden Şelalesi","Manavgat Şelalesi","Kapalıçarşı","Ölüdeniz","Kaçkar Dağları Milli Parkı","Kemeraltı"]:
    print(n, "->", wiki_coords(n))
