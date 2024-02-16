# -*- coding: utf-8 -*-

"""
    atcoder_tools.py

    this is a tool to automate getting and submitting a code.
    
    libraries:
        requests
        bs4

    start:
        sh start.sh
        python3 atcoder_tool.py

    environment:
        python3.11.6
"""


import requests
from bs4 import BeautifulSoup
from html.parser import HTMLParser
import re
import os
import shutil
import subprocess
import readline
import signal
import sys
import time
import datetime


color = {
    "CE":"\033[93mCE\033[0m",
    "MLE":"\033[93mMLE\033[0m",
    "TLE":"\033[93mTLE\033[0m",
    "RE":"\033[93mRE\033[0m",
    "OLE":"\033[93mOLE\033[0m",
    "IE":"\033[93mIE\033[0m",
    "WA":"\033[93mWA\033[0m",
    "AC":"\033[92mAC\033[0m",
    "WJ":"\033[36mWJ\033[0m",
    "WR":"\033[36mWR\033[0m"
}


def main():
    """ 
    entry point
    """
    atcoder = Atcoder()
    atcoder.login()
    while True:
        try:
            with open("./data/recent.txt",'r') as f:
                recent = f.read()
                atcoder.contest = input("♡ contest?(r for {}, q for quit) > ".format(recent))
                if(atcoder.contest == 'r'):
                    atcoder.contest = recent
        except FileNotFoundError:
            atcoder.contest = input("♡ contest?(q for quit)")
        if(atcoder.contest == "q"):
            sys.exit()
        if(atcoder.search_contest()):
            break
    while(True):
        command = input("♡ command?(m for help) > ")
        if(len(command)==0):
            pass
        elif(command == 'm'):
            print(
                '   Usage: tcode[a,b,..h(Ex)]   test code(dont need space)\n'\
                '      or: scode[a,b,..h(Ex)]   send code(dont need space)\n'\
                '      or: mcode[a,b...h(Ex)]   test code from file\n'\
                '      or: c                    check result\n'\
                '      or: exit                 exit        '
            )
        elif(command[0]=='t' and len(command)==2):
            atcoder.test_code(command[1])
        elif(command[0]=='s' and len(command)==2):
            atcoder.send_code(command[1])
        elif(command[0]=='c'):
            atcoder.check_code()
        elif(command[0]=='m'):
            atcoder.test_code_manually(command[1])
        elif(command=='exit' or command=='e'):
            break


def disable_ctrl_c(signal, frame):
    pass

signal.signal(signal.SIGINT, disable_ctrl_c)


def mkdir(path):
    """ 
    arguments   :   pass to directory. 
                    path = './abc222/testcase'
    return value:   If directory already exist, return True. else return False.
    description :   Create directory if it doesnt exist.
    """
    if not os.path.isdir(path):
        os.makedirs(path)
        return True
    else:
        return False


class Atcoder:
    """
    variables   :   self.contest = 'abc222'
                    self.linklist = ['/contests/abc222/tasks/abc222_a','...']
    description :   class for getting and maintaining contest data.
    """

    def __init__(self):
        self.contest = ""
        self.linklist = []
        self.session=requests.session()

    def search_contest(self):
        """ 
        arguments   :   none
        return value:   none
        description :   loop until a contest is found.
                        store contestname to self.contest.
                        self.contest = 'abc222'
        """
        response = requests.get("https://atcoder.jp/contests/{}/tasks".format(self.contest))
        if response.status_code == 200:
            print('    Contest {} found!'.format(self.contest))
            if(mkdir("./{}".format(self.contest))):
                self._get_question_list()
                self._get_io()
            mkdir("./data")
            with open("./data/recent.txt",'w') as f:
                f.write(self.contest)
            return True
        else:
            print('    Contest does not exist') 
            return False

    def _get_question_list(self):
        """ 
        arguments   :   none
        return value:   none
        description :   get question list.
                        store contest links to linklist.
                        self.linklist = ['/contests/abc222/tasks/abc222_a','...']
        """        
        data = {
            "csrf_token":self._get_csrf_token("https://atcoder.jp/contests/{}/tasks".format(self.contest))
        }
        response = self.session.get("https://atcoder.jp/contests/{}/tasks".format(self.contest), params=data)
        soup = BeautifulSoup(response.text, "html.parser")
        elems = soup.find_all(href=re.compile("/contests/{}/tasks/abc".format(self.contest)))
        for elem in elems:
            self.linklist.append(elem.attrs["href"])
        self.linklist = list(dict.fromkeys(self.linklist))

    def _get_io(self):
        """ 
        arguments   :   none
        return value:   none
        description :   create contest directory and get input,output list, copy template file.
                        structure:
                        abc222
                         - a.txt
                         - b.txt
                         - testcase
                           - a
                             - in
                               - 0.txt
                               - 1.txt
                             - out
                               - 0.txt
                               - 1.txt
        """
        mkdir("./{}/testcase".format(self.contest))

        for link in self.linklist:
            question = re.findall('.*_(.*)',link)
            mkdir("./{}/testcase/{}".format(self.contest,question[0]))
            mkdir("./{}/testcase/{}/in".format(self.contest,question[0]))
            mkdir("./{}/testcase/{}/out".format(self.contest,question[0]))
            data = {
                "csrf_token":self._get_csrf_token("https://atcoder.jp/{}".format(link))
            }
            response = self.session.get("https://atcoder.jp{}".format(link),params=data)
            soup = BeautifulSoup(response.text, "html.parser")
            iotmp = soup.find(class_='lang-ja').find_all('pre')
            iolist = []
            for io in iotmp:
                if(not (io.find('var'))):
                    iolist.append(io.text)
            i=0
            for io in iolist:
                if(i%2==0):
                    f = open("./{}/testcase/{}/in/{}.txt".format(self.contest,question[0],int(i/2)), 'w')
                    f.write(io)
                    f.close()
                else:
                    f = open("./{}/testcase/{}/out/{}.txt".format(self.contest,question[0],int(i/2)), 'w')
                    f.write(io)
                    f.close()
                i = i + 1
            shutil.copyfile("./template/{}.cpp".format(question[0]), "./{}/{}.cpp".format(self.contest,question[0]))

    def test_code(self,code):
        """ 
        arguments   :   code = [a,b,..h(Ex)] 
        return value:   none
        description :   test provided code
        """
        file_path = './{}/{}.cpp'.format(self.contest,code)
        try:
            input_files = os.listdir("./{}/testcase/{}/in".format(self.contest,code))
        except FileNotFoundError:
            print("question {} is nothing".format(code))
            return
        process = subprocess.Popen(['g++', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        ce = False
        error_text = ""
        if error:
            ce = True
            error_text = error.decode('utf-8')
            if error_text.endswith("\n"):
                error_text = error_text[:-1]
            print("Compilation failed:")
        else:
            print("Compilation successful")
        accnt = 0
        sum = 0
        tle = False
        for input_file in input_files:
            try:
                with open("./{}/testcase/{}/in/{}".format(self.contest,code,input_file), 'r') as f:
                    process = subprocess.Popen(['./a.out'], stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    start_time = time.time()
                    tlein = False
                    while process.poll() is None:
                        if time.time() - start_time > 3:
                            process.terminate()
                            tle = True
                            tlein = True
                            break
                    output, error = process.communicate()

                # Check if there was an error during execution
                infile = open("./{}/testcase/{}/in/{}".format(self.contest,code,input_file), 'r')
                outfile = open("./{}/testcase/{}/out/{}".format(self.contest,code,input_file), 'r')
                intext = infile.read()
                if intext.endswith("\n"):
                    intext = intext[:-1]
                answer = outfile.read()
                if answer.endswith("\n"):
                    answer = answer[:-1]
                if error:
                    print("Execution failed:")
                    error = error.decode('utf-8')
                    if error.endswith("\n"):
                        error = error[:-1]
                    print(error)
                    print("A:  {}".format(answer.replace("\n","\n    ")))
                    print("result: {} - {}\n".format(input_file,color["WA"]))
                else:
                    outtext = output.decode('utf-8')
                    if outtext.endswith("\n"):
                        outtext = outtext[:-1]
                    print("I:  {}\nO:  {}".format(intext.replace("\n","\n    "),outtext.replace("\n","\n    ")))
                    if(answer.replace("\n", "").rstrip() == output.decode().replace("\n", "").rstrip()):
                        print("result: {} - {}\n".format(input_file,color["AC"]))
                        accnt += 1
                    elif(tlein == True):
                        print("A:  {}".format(answer.replace("\n","\n    ")))
                        print("result: {} - {}\n".format(input_file,color["TLE"]))
                    else:
                        print("A:  {}".format(answer.replace("\n","\n    ")))
                        print("result: {} - {}\n".format(input_file,color["WA"]))
            except FileNotFoundError:
                print("Error: C++ executable file not found")
                break
            sum += 1
        if (ce == True):
            print(error_text)
            print("test result:    {} - {}".format(code,color["CE"]))
        elif (accnt == sum):
            print("test result:    {} - {}".format(code,color["AC"]))
        elif(tle == True):
            print("test result:    {} - {}".format(code,color["TLE"]))
        else:
            print("test result:    {} - {}".format(code,color["WA"]))
    
    def test_code_manually(self,code):
        """ 
        arguments   :   code = [a,b,..h(Ex)] 
        return value:   none
        description :   test provided code
        """
        file_path = './{}/{}.cpp'.format(self.contest,code)
        input_file = "./input.txt"
        try:
            process = subprocess.Popen(['g++', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            print("question {} is nothing".format(code))
            return
        output, error = process.communicate()
        if error:
            print("Compilation failed:")
            print(error.decode('utf-8'))
        else:
            print("Compilation successful")
        try:
            with open("./input.txt", 'r') as f:
                process = subprocess.Popen(['./a.out'], stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output, error = process.communicate()
            # Check if there was an error during execution
            if error:
                print("Execution failed:")
                print(error.decode('utf-8'))
            else:
                infile = open("./input.txt", 'r')
                intext = infile.read()
                if intext.endswith("\n"):
                    intext = intext[:-1]
                outtext = output.decode('utf-8')
                if outtext.endswith("\n"):
                    outtext = outtext[:-1]
                print("I:  {}\nO:  {}".format(intext.replace("\n","\n    "),outtext.replace("\n","\n    ")))
        except FileNotFoundError:
            print("Error: C++ executable file not found")
    
    def _get_csrf_token(self,url):
        """ 
        arguments   :   url(full)
        return value:   csrf_token(str)
        description :   get csrf_token for post data.
        """
        response = self.session.get(url)
        string = BeautifulSoup(response.text, 'html.parser')
        csrf_token = string.find(attrs={'name': 'csrf_token'}).get('value')
        return csrf_token

    def login(self):
        """ 
        arguments   :   none
        return value:   none
        description :   login
        """
        credentials = {}
        with open('./data/credentials.txt', 'r') as file:
            for line in file:
                key, value = line.strip().split(': ')
                credentials[key] = value
        data={
            "username":credentials["username"],
            "password":credentials["password"],
            "csrf_token": self._get_csrf_token("https://atcoder.jp/login")
        }
        response = self.session.post("https://atcoder.jp/login",data=data)

    def send_code(self,code):
        """ 
        arguments   :   code = [a,b,..h(Ex)] 
        return value:   none
        description :   send code
        """
        try:
            f = open("./{}/{}.cpp".format(self.contest,code),'r')
        except FileNotFoundError:
            print("question {} is nothing".format(code))
            return
        data = {
            "data.TaskScreenName":"{}_{}".format(self.contest,code),
            "data.LanguageId":"5001",
            "sourceCode":f.read(),
            "csrf_token":self._get_csrf_token("https://atcoder.jp/contests/{}/submit".format(self.contest))
        }
        f.close()
        response = self.session.post("https://atcoder.jp/contests/{}/submit".format(self.contest), params=data)
        print("Code sent!")
        self.check_code()

    def check_code(self):
        """ 
        arguments   :   code = [a,b,..h(Ex)] 
        return value:   none
        description :   check code
        """
        a = 0
        while(True):
            response = self.session.get("https://atcoder.jp/contests/{}/submissions/me".format(self.contest))
            soup = BeautifulSoup(response.text, "html.parser")
            submittions = soup.find_all('tr')
            info = [td.text for td in submittions[1].find_all('td')]
            try:
                if(info[7][0].isdigit()):
                    print('    {} - {} - {}'.format(info[1][0],color[info[6]],info[7]))
                    break
                elif(info[6]=="WJ"):
                    if(a%4 == 0):
                        print('    {} - {} ..'.format(info[1][0],color["WJ"]))
                    time.sleep(1)
                    a += 1
                else:
                    print('    {} - {}'.format(info[1][0],color[info[6]]))
                    break
            except KeyError:
                if(a%4 == 0):
                    print('    {} - {} judging..'.format(info[1][0],color["WJ"]))
                time.sleep(1)
                a += 1

if __name__ == "__main__":
    main()