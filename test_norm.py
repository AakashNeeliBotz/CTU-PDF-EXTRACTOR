from field_mappings import normalize_header

test_headers = [
    'Sl. No',
    'Type of \nProject',
    'Installed \ncapacity \n(MW)',
    'State \n(Connectivity \nStation)',
    'Expected date of \nconnectivity/ GNA to \nbe made effective',
    'Application ID',
    'Name of Applicant'
]

for header in test_headers:
    normalized = normalize_header(header)
    print(f'{header!r:60s} -> {normalized}')
