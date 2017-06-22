# getout
Programmatic API in Python to interact with CDMON domain provider website.

This is WIP but has already been used in production since two years ago.

See example.py and example_details.py for some tips about how to use.

All operations on domains must work except this ones:

  * Activate/deactivate private whois
  * Activate/deactivate autorenew domain
  
  
## Quickstart:

```
git clone https://github.com/EstudioNexos/getout.git
cd getout
pip install -r requirements.txt
touch myscript.py
```

And then in myscript.py:

```
from api import CDMON

cdmon = CDMON(user="yourcdmonuser",password="yourcdmonpassword")

print list(cdmon.get_summary())
```

Results from queries are Lookupy collections, this means that can be filtered using Lookupy expressions.
Check documentation for more ways of filtering: https://github.com/naiquevin/lookupy

```
summary.filter(canonical_name__endswith='.es')
```
## Contributing

Issues and contributions are welcomed

## DISCLAIMER

This project is not related in any way with cdmon.com or 10dencehispahard S.L.

CDMON is a 10dencehispahard S.L trademark.

This project doesn't use any data that cannot be obtained using a standard web browser.
