#!/usr/bin/env python3

import os
import json
import aria2p.options
import requests
import xmltodict
import uuid
from time import sleep
import aria2p
import html
import urllib.parse


def get_uuid(name, uuid_table_path):
    def write_uuid(_name):
        _uuid = str(uuid.uuid4())
        if os.path.exists(uuid_table_path):
            with open(uuid_table_path) as f:
                _uuid_table = json.loads(f.read())
            _uuid_table.update({_name: _uuid})
            with open(uuid_table_path, 'w') as f:
                f.write(json.dumps(_uuid_table))
        else:
            with open(uuid_table_path, 'w') as f:
                f.write(json.dumps({_name: _uuid}))
        return _uuid
    
    if os.path.exists(uuid_table_path):
        with open(uuid_table_path) as f:
            uuid_table = json.loads(f.read())
        if name in uuid_table:
            return uuid_table[name]
        else:
            return write_uuid(name)
    else:
        return write_uuid(name)


def compare_lists(local_list, upstream_list):
    added_items = [item for item in upstream_list if item not in local_list]
    
    modified_items = []
    for item in upstream_list:
        if item in local_list:
            local_item_index = local_list.index(item)
            if item != local_list[local_item_index]:
                modified_items.append((local_list[local_item_index], item))
    
    deleted_items = [item for item in local_list if item not in upstream_list]
    
    return added_items, modified_items, deleted_items


def parse_html(text):
    return html.escape(text)
    # return text.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')


def simplify_magnet_link(magnet_link):
    parsed_url = urllib.parse.urlparse(magnet_link)

    query_params = urllib.parse.parse_qs(parsed_url.query)
    xt_param = query_params.get('xt', [''])[0]
    # dn_param = query_params.get('dn', [''])[0]

    simplified_magnet_link = f"magnet:?xt={xt_param}"
    # if dn_param:
    #     simplified_magnet_link += f"&dn={dn_param}"
    
    return simplified_magnet_link


def push_to_telegram(config, message, proxies):
    api_url = f"https://api.telegram.org/bot{config['token']}/sendMessage"

    payload = {
        "chat_id": config['chat_id'],
        "text": message,
        "parse_mode": "HTML",
        "link_preview_options": {
            "is_disabled": True
        }
    }

    response = requests.post(api_url, json=payload, timeout=config['timeout'], proxies=proxies)
    return response.json()


def win32_namespace_compatible(text):
    def half2full(s):
        '''
        Convert all ASCII characters to the full-width counterpart.
        https://stackoverflow.com/a/36693548
        '''
        HALF2FULL = dict((i, i + 0xFEE0) for i in range(0x21, 0x7F))
        HALF2FULL[0x20] = 0x3000
        return str(s).translate(HALF2FULL)
    
    foo = r'/\:*"?<>|'
    for _ in foo:
        if _ in text:
            text = text.replace(_, half2full(_))

    return text


def push_magnet_to_aria2_rpc(config, magnet, bangumi_name):
    config['options']['dir'] = config['options']['dir'].replace(r'{bangumi_name}',
                                                                win32_namespace_compatible(bangumi_name))

    aria2 = aria2p.API(aria2p.Client(
            host=config['host'], port=config['port'], secret=config['secret'], timeout=config['timeout']))
    return aria2.add_magnet(magnet, options=config['options'])


def main():
    cd = os.path.split(os.path.realpath(__file__))[0]
    config_path = os.path.join(cd, 'config.json')
    uuid_table_path = os.path.join(cd, 'data', 'uuid_table.json')

    with open(config_path) as f:
        config = json.loads(f.read())

    bangumi_list = config['bangumi']['list']
    config_aria2_rpc = config['aria2_rpc']
    config_telegram = config['telegram']
    config_proxies = config['proxies']

    for bangumi in bangumi_list:
        data_file = os.path.join(cd, 'data', '{}.json'.format(get_uuid(bangumi['name'], uuid_table_path)))

        if os.path.exists(data_file):
            with open(data_file) as f:
                local_result_json = f.read()
                local_result_list = json.loads(local_result_json)
        else:
            local_result_json = ''
            local_result_list = []
        
        _xml = requests.get(url=bangumi['upstream-url'], timeout=config['bangumi']['timeout'], proxies=config_proxies).text
        upstream_result_list = xmltodict.parse(_xml)['rss']['channel']['item']
        upstream_result_json = json.dumps(upstream_result_list)

        added, modified, deleted = compare_lists(local_result_list, upstream_result_list)

        if added == []:
            reaction = '[ T_T ]'
            message = 'There is no update for {}'.format(bangumi['name'])
            print(f'{reaction} {message}')
        else:
            # print(added)
            reaction = '[ >w< ]'
            message = '{} Update{} for {}'.format(len(added), 's' if len(added) > 1 else '', bangumi['name'])
            print(f'{reaction} {message}')

            tg_msgs = []

            for _ in added:
                webpage = parse_html(_['link'])
                magnet = simplify_magnet_link(parse_html(_['enclosure']['@url']))

                push_magnet_to_aria2_rpc(config=config_aria2_rpc, magnet=magnet, bangumi_name=bangumi['name'])

                msg = (
                    f"{_['title']}\n"
                    f"Poster: {_['author']}\n"
                    f"Date: {_['pubDate']}\n"
                    f"🔗 <a href='{webpage}'>Webpage</a>\n"
                    f"🧲 <code>{magnet}</code>"
                )
                tg_msgs.append(msg)

            tg_msgs.append(parse_html(message))
                
            for _ in tg_msgs:
                push_to_telegram(config=config_telegram, message=_, proxies=config_proxies)
                sleep(1)
            
            with open(data_file, 'w') as f:
                f.write(upstream_result_json)

        sleep(1)


if __name__ == '__main__':
    main()