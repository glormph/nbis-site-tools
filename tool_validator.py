import json
import urllib2
import yaml
import sys
#import bibtexparser


BIO_TOOLS_URL = 'https://bio.tools/api/tool/{}/?format=json'
DOI_URL = 'http://dx.doi.org/{}'

# Which fields are required:
fields_not_in_biotools = [# first the fields unknown to bio.tools
                          'pi', 'devstatus', 'released', 'releasedate',
                          'affiliation',  # too complex to parse from bio.tools
                          # doi fields contains DOIs of desired publications
                          # to display on website. These may not be the same as
                          # on bio.tools because of display space
                          'primary_doi', 'uses_doi',
                          # for downloading the tool JSON
                          'biotools_id']
                          #'biotools_version'] # Optional, required only for some tools
# following fields MUST be in bio.tools entry
biotools_required_fields = ['name', 'version', 'homepage', 'description',
                            'operatingSystem', 'toolType']
biotools_required_contact = ['url', 'email']  # will ok either


stubfile = sys.argv[1]

with open(stubfile) as fp:
    stub = json.load(fp)
output_yml = {}

# check if all the "extra fields" are in there
for field in fields_not_in_biotools:
    try:
        output_yml[field] = stub[field]
    except KeyError:
        print('Could not find field {} in stub file. Please make sure all '
              'fields {} are in the file'.format(field, fields_not_in_biotools))
        sys.exit(1)
print(output_yml)

# download bio.tools JSON
if 'biotools_version' in stub:
    biotools_url_id = '{}/version/{}'.format(output_yml['biotools_id'],
                                             stub['biotools_version'])
else:
    biotools_url_id = output_yml['biotools_id']
tool_url = BIO_TOOLS_URL.format(biotools_url_id)
try:
    biotools_json = json.loads(urllib2.urlopen(tool_url).read())
except urllib2.HTTPError:
    print('URL {} to bio.tools did not resolve. Please make sure the tool '
          'ID is correct. If you are not passing a version number, you '
          'may try to do so instead (but for most tools that should be '
          'fine)'.format(tool_url))
    sys.exit(1)
except ValueError:
    print('No correct JSON was returned when querying {}'.format(tool_url))
    sys.exit(1)

# validate fields in bio.tools JSON
for field in biotools_required_fields:
    try:
        output_yml[field] = biotools_json[field]
    except KeyError:
        print('JSON from bio.tools does not contain the field: {}. Please make '
              'sure all fields {} are in the '
              'bio.tools registry'.format(field, biotools_required_fields))
        sys.exit(1)

contact_success = False
for field in biotools_required_contact:
    cfield = 'contact_{}'.format(field)
    try:
        output_yml[cfield] = biotools_json['contact'][0][field]
    except KeyError:
        pass
    else:
        if output_yml[cfield] is not None:
            contact_success = True
if not contact_success:
    print('Could not find either contactEmail or contactURL in bio.tools JSON')
    sys.exit(1)


# Get bibtex from DOIs for publications
# curl -L -H "Accept: application/x-bibtex; charset=utf-8" http://dx.doi.org/$1
def get_bibtex(doi):
    url = DOI_URL.format(doi)
    req = urllib2.Request(url, headers={'Accept':
                                        'application/x-bibtex; charset=utf-8'})
    return urllib2.urlopen(req).read()


def get_json_doi(doi):
    url = DOI_URL.format(doi)
    req = urllib2.Request(url, headers={'Accept':
                                        'application/json; charset=utf-8'})
    return json.loads(urllib2.urlopen(req).read())


def parse_bibtex_to_authornames(doidata):
    authors_family_names = [x['family'] for x in doidata['author']]
    authortxt = authors_family_names[0]
    if len(authors_family_names) > 2:
        authortxt = '{} et al.'.format(authortxt)
    elif len(authors_family_names) == 2:
        authortxt = '{} & {}'.format(authortxt, authors_family_names[1])
    authortxt = '{}, {}'.format(authortxt,
                                doidata['issued']['date-parts'][0][0])
    return authortxt

output_yml['primary_pub'] = []
for tooldoi in output_yml['primary_doi']:
    doidata = get_json_doi(tooldoi)
    # in case we switch back to bibtex, this can be here.
    #bibpub = bibtexparser.loads(bibtex).entries[0]
    #article_id = bibpub['ID'].split('_')
    authortxt = parse_bibtex_to_authornames(doidata)
    output_yml['primary_pub'].append(authortxt)

output_yml['uses_pub'] = []
for usesdoi in output_yml['uses_doi']:
    doidata = get_json_doi(usesdoi)
    authortxt = parse_bibtex_to_authornames(doidata)
    output_yml['uses_pub'].append(authortxt)


releasedate = output_yml.pop('releasedate')
# write YAML
outfile = '{}.yml'.format(stub['biotools_id'])
with open(outfile, 'w') as fp:
    fp.write('---\n')
    fp.write('releasedate: {}\n'.format(releasedate))
    yaml.safe_dump(output_yml, fp, encoding='utf-8')

print('Done, wrote output to {}'.format(outfile))
