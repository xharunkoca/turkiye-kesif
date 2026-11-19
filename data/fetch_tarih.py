from fetch import cached
from fetch_v2 import TPL, DISTRICT, PROVINCE, GEO
groups = [["Q35112127","Q23413","Q57831"], ["Q12280","Q522124","Q186347"], ["Q28077","Q57346","Q838858","Q132834"]]
for i,g in enumerate(groups):
    vals=" ".join(f"wd:{c}" for c in g)
    cached(f"v2x_tarih{i}_d", TPL % (DISTRICT % vals))
    cached(f"v2x_tarih{i}_p", TPL % (PROVINCE % vals))
    cached(f"v2x_tarih{i}_g", GEO % vals)
