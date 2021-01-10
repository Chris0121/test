# -*- coding: utf-8 -*-
import psycopg2
import os
import json
import pandas as pd
import urllib
import commands
import shlex
import datetime
import json
import sys
import time
from selenium.webdriver.chrome.options import Options
from selenium import webdriver


class Sentry:
    def __init__(self, base_url, token):
        self.baseUrl = base_url
        self.token = token

    def _create_url(self, route_url):
        url = self.baseUrl + route_url
        return url

    @staticmethod
    def escape_url(url):
        print ("start escasp url")
        print ("before : " + url)
        url = urllib.quote(url)
        print ("after : " + url)
        return url

    def _create_curl_cmd(self, url):
        print ("start create curl cmd")
        cmd = "curl '" + url + "' -H 'Authorization: Bearer " + self.token + "'"
        print ("curl cmd is : %s" % cmd)
        return cmd

    def _create_curl_cmd_list(self, url):
        print ("=== start create curl cmd list ===")
        cmd = self._create_curl_cmd(url)
        cmd_list = [cmd]
        check_cursor_cmd = cmd + " -i -s | grep Link | awk -F ' ' '{print $8}' | awk -F '\"' '{print $2}' | xargs echo -n"
        print check_cursor_cmd
        check_cursor_cmd_result = os.popen(check_cursor_cmd).read()
        print check_cursor_cmd_result
        if check_cursor_cmd_result == "true":
            print 'check_cursor_cmd_result is true:'
            get_cmd = cmd + " -i -s | grep Link | awk -F ' ' '{print $6}' | awk -F '<' '{print $2}' | awk -F '>' '{print $1}' | xargs echo -n"
            get_cmd_result = os.popen(get_cmd).read()  # url contains cursor
            print "get_cmd_result:"
            print get_cmd_result
            cmd_list.extend(self._create_curl_cmd_list(get_cmd_result))
            return cmd_list
        print ("= end create curl cmd list =")
        print ("curl cmd list is : %s" % cmd_list)
        return cmd_list

    @staticmethod
    def run_cmd(cmd):
        tmp_res = os.popen(cmd).read()
        tmp_res = json.loads(tmp_res)
        return tmp_res

    def get_issues(self, route_url):
        url = self._create_url(route_url)
        cmd_list = self._create_curl_cmd_list(url)
        print "=== start get issues from cmd_list ==="
        issues = []
        for cmd in cmd_list:
            res = self.run_cmd(cmd)
            issues.extend(res)
        print ("len(issues) is : %d" % len(issues))
        print "= end get issues from cmd_list ="
        return issues


class IssueCsv:
    def __init__(self, name):
        print "init csv"


if __name__ == '__main__':
    print ("======*** start load config ***======")
    with open("config.json", 'r') as load_f:
        config_dict = json.load(load_f)
        print(config_dict)
    print ("======* end load config *======")

    print ("======*** start init ***======")
    base_url = config_dict['project']['jerry-backend']['config']['base_url']
    token = config_dict['project']['jerry-backend']['config']['token']
    sentry = Sentry(base_url, token)
    base_issues_url_list = config_dict['project']['jerry-backend']['config']['base_issues_url_list']
    print ("======* end init *======")

    print ("======*** start init query issues ***======")
    query_dict = config_dict['project']['jerry-backend']['query_issues']
    print query_dict
    date = datetime.datetime.now().strftime('%Y/%m/%d')
    print date
    print ("======* end init query issues *======")

    conn = psycopg2.connect(database="jerry_test", user="jerry_test", password="jerry_test", host="127.0.0.1",
                            port="5432")
    cursor = conn.cursor()
    sql = """INSERT INTO sentry_issues (date, project, team, owner, title, status) VALUES (%(date)s, %(project)s, %(team)s, %(owner)s, %(title)s, %(status)s)"""
    print ("======*** start insert csv ***======")
    for key in query_dict:
        print ("open csv name : %s" % (str(key) + ".csv"))
        df = pd.read_csv(key + ".csv", header=0, squeeze=True)
        row = len(df)
        print ("df len is : %s" % row)
        df.ix[row, 'date'] = date
        for member in query_dict[key]:
            counter = 0
            for base_issues_url in base_issues_url_list:
                issue_list = sentry.get_issues(base_issues_url + sentry.escape_url(query_dict[key][member]))
                for issue in issue_list:
                    print("===1====")
                    print issue
                    owner = 'None'
                    team = 'false'
                    print type(issue['assignedTo'])
                    if(issue['assignedTo'] != None):
                        print issue['assignedTo']
                        owner = str(issue['assignedTo']['name']).split('@')[0]
                        if (issue['assignedTo']['type'] == 'team'):
                            team = 'true'
                    project = str(base_issues_url).split('/')[2]
                    print("=====333====")
                    print project
                    print("===111===")
                    params = {'date': date, 'project': project, 'team': team, 'owner': owner, 'title': issue['title'], 'status': issue['status']}
                    cursor.execute(sql, params)
                    print("successfully")
                    conn.commit()
                    print issue['metadata']
                    print("====2===")
                # counter = counter + len(sentry.get_issues(base_issues_url + sentry.escape_url(query_dict[key][member])))
            df.ix[row, member] = counter
        df.to_csv(key + ".csv", index=False)
    print ("======* end insert csv *======")
#
#     data_list = config_dict['project']['jerry-backend']['query_issues'].keys()
#     print data_list
#     data = {"data": []}
#     print ("======*** start create data ***======")
#     for m in data_list:
#         print ("open csv name : %s" % (str(m) + ".csv"))
#         df = pd.read_csv(str(m) + ".csv", header=0, squeeze=True)
#         day_len = len(df['date'])
#         print ("day_len : %s" % day_len)
#         count = 0
#         day_count = 30
#         if day_len > day_count:
#             count = day_count
#         else:
#             count = day_len
#         print ("count is : %d" % count)
#         date_serious = []
#         data_serious = []
#         for i in df.columns.values:
#             if i == "date":
#                 for ii in range(count):
#                     date_serious.append(df['date'][(len(df['date']) - 1) - count + (ii + 1)])
#             else:
#                 data_serious_data = []
#                 for j in range(count):
#                     data_serious_data.append(df[i][(len(df['date']) - 1) - count + (j + 1)])
#                 data_serious.append({'name': i, 'data': data_serious_data})
#
#         print ("date_serious is :")
#         print date_serious
#         print ("data_serious is :")
#         print data_serious
#         data['data'].append({m: {"date_series": date_serious, "data_series": data_serious}})
#     print ("data is :")
#     print data
#     # print ("start create team total data")
#     # data_serious = []
#     # date_serious = []
#     # for i in data['data']:
#     #     data_serious_data = []
#     #     date_serious = []
#     #     for ii in range(0, 30):
#     #         data_serious_data.append(0)
#     #     print data_serious_data
#     #     for k in i:
#     #         date_serious = i[k]['date_series']
#     #         for j in i[k]['data_series']:
#     #             count = 0
#     #             for i in j['data']:
#     #                 data_serious_data[count] = data_serious_data[count] + i
#     #                 count = count + 1
#     #     print ('data_serious_data_total')
#     #     print data_serious_data
#     #     data_serious.append({'name': k, 'data': data_serious_data})
#     #     print date_serious
#     #     print len(data_serious_data)
#     # data['data'].append({"team": {"date_series": date_serious, "data_series": data_serious}})
#     # print ("end team total data")
#     date_replace = json.dumps(data)
#     print date_replace
#     cmd = ""
#     if "darwin" == sys.platform :
#         cmd = "sed -i '' 's#data_replace#" + date_replace + "#g' index2.html"
#     else:
#         cmd = "sed -i 's#data_replace#" + date_replace + "#g' index2.html"
#     print cmd
#     os.popen(cmd)
#     print ("======* end create data *======")
#     os.popen("cp index2.html index.html")
#     os.popen("cp index.backup.html index2.html")
# #     print ("======*** create report png ***======")
# #     chrome_options = Options()
# #     chrome_options.add_argument('--headless')
# #     chrome_options.add_argument('--disable-gpu')
# #     print os.getcwd()
# #     driverChrome = webdriver.Chrome(executable_path=os.getcwd() + "/chromedriver", chrome_options=chrome_options)
# #     driverChrome.get("file://" + os.getcwd() + "/index.html")
# #     width = driverChrome.execute_script("return document.documentElement.scrollWidth")
# #     height = driverChrome.execute_script("return document.documentElement.scrollHeight")
# #     print(width, height)
# #     driverChrome.set_window_size(width, height)
# #     time.sleep(10)
# #     driverChrome.save_screenshot('report.png')
# #     time.sleep(10)
# #     driverChrome.close()
# #     print ("======* end report png *======")


