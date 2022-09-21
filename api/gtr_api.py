#!/usr/bin/env python

import requests
import json
import sys
import os
import argparse

script = sys.argv[0]
base_url="https://submit.ncbi.nlm.nih.gov"
gtr_headers = {
    'Content-Type': 'application/json',
    'SP-API-KEY': 'YOUR-API-KEY'
}

def get_parameters(actions):
    parser = argparse.ArgumentParser(
        prog=os.path.basename(script),
        description="Script to call GTR api endpoints")

    parser.add_argument('action', nargs='?', help='action to perform',
                        choices=actions)
    parser.add_argument('mode', nargs='?', help='submission mode',
                        choices=['api', 'apitest'])
    parser.add_argument('additional_data', nargs='?', help='additional data to perform the action.\n'
                        'For gtr_sub_api or dry_run, this is the json file.\n'
                        'For gtr_get_action, this is the submission ID.\n'
                        'For multi_subs, this is the text file of json file name list.\n'
                        'For multi_deletes, this is the text file of GTR accession list.')
    args = parser.parse_args()
    if not args.mode:
        print('mode and additional data are required.\n', file=sys.stderr)
        parser.print_help(sys.stderr)
        sys.exit(1)
    elif not args.additional_data:
        print('additional data is required.\n', file=sys.stderr)
        parser.print_help(sys.stderr)
        sys.exit(1)

    return (args.action, args.mode, args.additional_data)

def gtr_sub_api_json(mode, json_data, **kwargs):
    url = f'{base_url}/{mode}/v1/submissions/'
    if 'dry_run' in kwargs and kwargs.get('dry_run'):
        url = url + '?dry-run=true'
    post_data_obj = {
        'actions': [{'type':'AddData', 'targetDb':'GTR', 'data':{ 'content':json_data }}]
    }
    response = requests.post(url, data=json.dumps(post_data_obj), headers=gtr_headers)
    json_out = kwargs
    json_out["status"] = response.status_code
    if response.text:
        json_out.update(response.json())
    print(json.dumps(json_out))
    return 0

def gtr_sub_api(mode, json_file):
    json_data = {}
    with open(json_file) as jf:
        json_data = json.load(jf)
    gtr_sub_api_json(mode, json_data, file=json_file)

def dry_run(mode, json_file):
    json_data = {}
    with open(json_file) as jf:
        json_data = json.load(jf)
    gtr_sub_api_json(mode, json_data, file=json_file, dry_run=True)

def gtr_get_action(mode, sub_id):
    url = f'{base_url}/{mode}/v1/submissions/{sub_id}/actions/'
    response = requests.get(url, headers=gtr_headers)
    print(response.text)
    return 0

def multi_subs(mode, json_list_file):
    file_list = []
    with open(json_list_file, 'r') as fl:
        file_list = fl.readlines()
    for f in file_list:
        if f.strip():
            gtr_sub_api(mode, f.strip())

def multi_deletes(mode, acc_list_file):
    acc_list = []
    with open(acc_list_file, 'r') as fl:
        acc_list = fl.readlines()
    for acc in acc_list:
        acc = acc.strip()
        if not acc:
            continue
        json_data = {"testDeletion": { "gtrAccession": acc } }
        gtr_sub_api_json(mode, json_data, gtrAccession=acc)

def main():
    cmd2process = {
        "gtr_sub_api": gtr_sub_api,
        "gtr_get_action": gtr_get_action,
        "multi_subs": multi_subs,
        "multi_deletes": multi_deletes,
        "dry_run": dry_run,
    }
    (action, mode, additional_data) = get_parameters(cmd2process.keys())
    return cmd2process[action](mode, additional_data)

if __name__ == "__main__":
    sys.exit(main())

