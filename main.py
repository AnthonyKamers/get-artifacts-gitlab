import os
import requests
import re
import markdown
import mechanize

def login_and_download(url, user, password):
    try:
        # login into the gitlab page
        browser = mechanize.Browser()
        browser.set_handle_robots(False)
        browser.open(url)

        browser.select_form(id = 'new_user')
        browser['user[login]'] = user
        browser['user[password]'] = password
        
        response = browser.submit()

        # get name of the file (last part of URL)
        filename = url.split('/')[-1]
        filepath = f'files/{filename}'

        # check if directory of the files exists
        if not (os.path.exists('files')):
            os.mkdir('files')
        
        # check if the file already exists in the directory
        if not (os.path.exists(filepath)):
            # write it to disk
            with open(filepath, 'wb') as f:
                f.write(response.get_data())
    except:
        pass

def run_issues(project_id, headers, params, user, password):
    # get all the issues
    url = f"https://gitlab.labsec.ufsc.br/api/v4/projects/{project_id}/issues"
    issues = requests.get(url, headers=headers, params=params).json()
    
    if (issues == []):
        return True

    # if is only one issue, transform it to list
    if (str(issues).startswith('[')):
        pass
    else:
        issues = [issues]

    # get all the links from the markdown
    links_all = []
    for issue in issues:
        description = issue['description']

        # transform markdown to html and get the links in it
        html = markdown.markdown(description, output_format='html')
        links = list(set(re.findall(r'href=[\'"]?([^\'" >]+)', html)))
        links = list(filter(lambda l: l[0] != "{", links))

        links_all = links_all + links

    # run through all the links and parse them
    # if there is an accepted file in the URL, 
    # download it
    accepted_files = ('.pdf', '.xml', '.p7s', '.dat')
    rejected_urls = ('https://www.etsi.org')
    for link in links_all:
        if (str(link).startswith(rejected_urls)):
            pass

        elif (str(link).endswith(accepted_files)):
            full_url = link
            if (str(link).startswith("/uploads") or str(link).startswith("/files")):
                full_url = f'https://gitlab.labsec.ufsc.br/pbad/codigos-de-referencia{link}'
            
            login_and_download(full_url, user, password)

    return False

def main():
    # get login information from txt file (login.txt)
    with open('login.txt') as login_file:
        lines = login_file.readlines()
        user = lines[0].replace("\n", "")
        password = lines[1]

    # get access token of gitlab from txt file (named access_token_gitlab.txt)
    with open("access_token_gitlab.txt") as file:
        access_token = file.readlines()[0]

    # PBAD - Codigos de Referencia
    project_id = 7

    # Use access token in the header, to validate requests
    headers = {'PRIVATE-TOKEN': access_token}

    # pagination (because gitlab obligates that)
    params = {'page': 1, 'per_page': 100}

    # while there are results, run the issues request
    while True:
        print(params)
        must_break = run_issues(project_id, headers, params, user, password)
        
        if must_break:
            break
        else:
            params['page'] += 1


if __name__ == "__main__":
    main()